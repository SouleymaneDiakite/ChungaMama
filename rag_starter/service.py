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
from fastapi import FastAPI
from pydantic import BaseModel

from rag_core import (
    build_system_prompt,
    detect_language,
    generate_text,
    get_store,
    requested_translation_language,
    retrieve,
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
    if translation_target and history.get("context"):
        prior_risk = history.get("classification", {}).get("risk_level", "low")
        system_prompt = build_system_prompt(history["context"], translation_target, prior_risk)
        reply = generate_text(system_prompt, history["question"])
        history["last_language"] = translation_target
        classification = history.get("classification", {
            "intent": "UNKNOWN", "entities": {}, "risk_level": "low", "escalate": False,
        })
        return ChatResponse(reply=reply, **classification)

    target_language = detect_language(question)
    retrieved = retrieve(_store, question, prior_question=history.get("question"))
    classification = retrieved["classification"]

    system_prompt = build_system_prompt(
        retrieved["context"], target_language, classification["risk_level"]
    )
    reply = generate_text(system_prompt, question)

    history["context"] = retrieved["context"]
    history["question"] = question
    history["last_language"] = target_language
    history["classification"] = classification

    return ChatResponse(reply=reply, **classification)


@app.get("/health")
def health():
    return {"status": "ok"}
