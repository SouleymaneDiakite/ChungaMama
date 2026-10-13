import uuid
import httpx
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models.escalation import Escalation

router = APIRouter()


class AssistantMessage(BaseModel):
    role: str
    content: str


class AssistantRequest(BaseModel):
    patient_id: str | None = None
    # Identifies one conversation on the assistant service. Separate from
    # patient_id on purpose: patient_id must be a real patients.id (it becomes
    # a foreign key on escalations), while the frontend can send a random
    # per-tab id for visitors who aren't linked to a patient record.
    session_id: str | None = None
    messages: list[AssistantMessage]


# This router is intentionally thin: ChungaMama owns patient records and
# auth; the assistant service (rag_starter/service.py) owns everything
# about understanding and responding to the message. Keeping it behind
# this HTTP boundary, rather than importing it directly, means whatever
# runs behind ASSISTANT_SERVICE_URL can change — a different retrieval
# setup, a different model, eventually a fine-tuned pipeline — without
# this router ever needing to change. Contract: {messages} -> {intent,
# entities, risk_level, reply, escalate}.
@router.post("/chat")
async def chat(payload: AssistantRequest, db: Session = Depends(get_db)):
    # session_id is what keys conversation history (retrieved context,
    # last answer language, risk level) on the assistant service side, so
    # translation follow-ups ("say that in English") re-ground on the
    # right patient's own prior turn. Without this, every request fell
    # back to the service's default session key and ALL patients shared
    # one conversation history — patient B's "translate that" could have
    # regenerated patient A's answer. Falls back to "anonymous" only for
    # a chat with no patient attached yet (e.g. a pre-registration demo).
    #
    # timeout=180.0 — confirmed via `ollama ps` that generation on this
    # CPU-only machine genuinely runs that long under load; 90s was still
    # too short and killed a request while Ollama was actively still
    # computing (100% CPU, not stuck). This is real hardware latency, not
    # a bug — it will drop sharply once generation runs on the GPU machine
    # instead of CPU. Lower this back down once that happens; a long
    # timeout here is a workaround for slow hardware, not a setting to
    # keep forever.
    async with httpx.AsyncClient(timeout=180.0) as client:
        try:
            resp = await client.post(
                settings.ASSISTANT_SERVICE_URL,
                json={
                    "messages": [m.model_dump() for m in payload.messages],
                    "session_id": payload.session_id or payload.patient_id or "anonymous",
                },
            )
            resp.raise_for_status()
        except httpx.HTTPError as e:
            raise HTTPException(502, f"Assistant service unavailable: {e}")

    result = resp.json()

    if result.get("escalate"):
        last_user_message = next(
            (m.content for m in reversed(payload.messages) if m.role == "user"), ""
        )
        patient_uuid = None
        if payload.patient_id:
            try:
                patient_uuid = uuid.UUID(payload.patient_id)
            except ValueError:
                patient_uuid = None  # don't fail the whole request over a bad id

        escalation = Escalation(
            patient_id=patient_uuid,
            intent=result.get("intent"),
            risk_level=result.get("risk_level", "high"),
            summary=(
                f"Situation: {last_user_message}\n"
                f"Assessment: {result.get('intent')} \u2014 risk level {result.get('risk_level')}\n"
                f"Recommendation: {result.get('reply')}"
            ),
        )
        db.add(escalation)
        db.commit()

    return result


# Voice input: forwards the recorded audio to the assistant service's
# /transcribe and returns {"text": ...}. It does NOT send the text on to /chat;
# the frontend shows it in the input box so the person can correct a
# mis-heard word before it's treated as their question.
# The URL is derived from ASSISTANT_SERVICE_URL so there is still one setting.
@router.post("/transcribe")
async def transcribe(audio: UploadFile = File(...), language: str = Form("sw")):
    url = settings.ASSISTANT_SERVICE_URL.rsplit("/chat", 1)[0] + "/transcribe"
    data = await audio.read()
    # Generous timeout: the first call loads the ASR model (and may download
    # it), which can take minutes. Later calls are fast on GPU.
    async with httpx.AsyncClient(timeout=300.0) as client:
        try:
            resp = await client.post(
                url,
                files={"audio": (audio.filename or "recording.wav", data,
                                 audio.content_type or "audio/wav")},
                data={"language": language},
            )
            resp.raise_for_status()
        except httpx.HTTPError as e:
            raise HTTPException(502, f"Transcription service unavailable: {e}")
    return resp.json()
