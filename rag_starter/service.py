"""
The actual network boundary: exposes POST /chat so
backend/app/routers/assistant.py can call this exactly like it would call
any other ASSISTANT_SERVICE_URL, fulfilling the contract from
HANDOVER.md: {messages} -> {intent, entities, risk_level, reply, escalate}.

This is Phase 0 of the project plan: wrap the cheap implementation behind
the real contract NOW, so the backend never has to change again no matter
what gets swapped behind this line later (embedding model, classifier,
LLM, ASR, TTS).

Run with:
    uvicorn service:app --host 0.0.0.0 --port 9000

Then point backend/.env's ASSISTANT_SERVICE_URL at
http://localhost:9000/chat (its default already matches).
"""
import os
import shutil
import tempfile

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from rag_core import (
    NO_INFO,
    NOTHING_TO_TRANSLATE,
    TRANSLATION_FAILED,
    build_system_prompt,
    detect_language,
    ensure_language,
    generate_text,
    get_store,
    requested_translation_language,
    retrieve,
    translate_reply,
    with_urgent,
    update_profile,
)

app = FastAPI(title="ChungaMama assistant service")

# In-memory session history, keyed by whatever the caller sends as
# `session_id`. This is intentionally the simplest possible thing that
# lets translation follow-ups ("say that in English") work across two
# HTTP calls — it is NOT persisted and resets on restart. If the backend
# needs this to survive restarts or scale across multiple instances later,
# swap this dict for a Redis/DB-backed store; nothing else in this file
# needs to change, because everything reads/writes through
# `_session_history(session_id)`.
_HISTORY: dict[str, dict] = {}


def _session_history(session_id: str) -> dict:
    return _HISTORY.setdefault(session_id, {})


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: list[Message]
    session_id: str = "default"


class ChatResponse(BaseModel):
    intent: str
    entities: dict
    risk_level: str
    reply: str
    escalate: bool


@app.on_event("startup")
def _load_store():
    # Loaded once at startup, not per-request — embedding model + DB
    # connection setup is expensive enough that doing it per-request would
    # make every single chat call slow.
    global _store
    _store = get_store()


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    # Only the latest user message is treated as "the question" — matches
    # query.py's one-question-at-a-time model. If the backend starts
    # sending full multi-turn message lists, this is the one place that
    # would need to grow to actually read prior turns instead of just the
    # last one.
    question = request.messages[-1].content
    history = _session_history(request.session_id)

    translation_target = requested_translation_language(
        question, history.get("last_language")
    )
    if translation_target:
        replies = history.get("replies")
        if not replies:
            # Nothing to translate. Do NOT fall through to retrieval:
            # searching for "translate to en" returns unrelated chunks and
            # the model makes something up from them.
            return ChatResponse(
                intent="UNKNOWN", entities={}, risk_level="low", escalate=False,
                reply=NOTHING_TO_TRANSLATE[translation_target],
            )
        prior = history.get("classification", {})
        reply = translate_reply(
            history, translation_target, generate_text, prior.get("risk_level", "low")
        )
        if reply is None:
            reply = TRANSLATION_FAILED[translation_target]
        else:
            history["last_language"] = translation_target
        classification = dict(history.get("classification", {
            "intent": "UNKNOWN", "entities": {}, "risk_level": "low", "escalate": False,
        }))
        # Keep the risk level, but never re-escalate: the original answer
        # already created the escalation, and the backend creates a new
        # Escalation row every time it sees escalate=true.
        classification["escalate"] = False
        if reply not in (TRANSLATION_FAILED["sw"], TRANSLATION_FAILED["en"]):
            reply = with_urgent(reply, translation_target, classification["risk_level"])
        return ChatResponse(reply=reply, **classification)

    target_language = detect_language(question)
    retrieved = retrieve(_store, question, prior_question=history.get("question"))
    classification = retrieved["classification"]

    # Remember what she told us (pregnant, how far along) so follow-ups like
    # "it's been 4 hours" still know it, and tell the model, so sources about
    # other situations (e.g. after birth) are not applied to her.
    profile = update_profile(history.get("profile", {}), classification["entities"])

    if not retrieved["covered"]:
        # Nothing in the knowledge base is close enough. Say so (fixed text)
        # instead of letting the model answer from the nearest unrelated chunk.
        reply = NO_INFO[target_language]
    else:
        system_prompt = build_system_prompt(
            retrieved["context"], target_language, classification["risk_level"], profile
        )
        # An English question can still come back in Swahili (the sources are
        # Swahili); ensure_language() translates if so.
        reply = ensure_language(generate_text(system_prompt, question), target_language)

    history["context"] = retrieved["context"]
    history["question"] = question
    history["last_language"] = target_language
    history["classification"] = classification
    history["profile"] = profile
    history["replies"] = {target_language: reply}  # stored WITHOUT the urgent line

    shown = reply if not retrieved["covered"] else with_urgent(
        reply, target_language, classification["risk_level"])
    return ChatResponse(reply=shown, **classification)


class TranscribeResponse(BaseModel):
    text: str


@app.post("/transcribe", response_model=TranscribeResponse)
def transcribe_audio(audio: UploadFile = File(...), language: str = Form("sw")) -> TranscribeResponse:
    """Audio in, text out. Deliberately does NOT answer the question: the
    frontend puts the transcript in the input box so the person can check
    and correct it before sending. For a medical assistant, a mis-heard word
    silently turning into advice is the worse failure."""
    from asr import transcribe  # lazy: keeps chat startup fast, see asr.py

    suffix = os.path.splitext(audio.filename or "")[1] or ".wav"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(audio.file, tmp)
        path = tmp.name
    try:
        return TranscribeResponse(text=transcribe(path, language))
    except Exception as e:
        raise HTTPException(500, f"Transcription failed: {e}")
    finally:
        os.remove(path)


@app.get("/health")
def health():
    return {"status": "ok"}
