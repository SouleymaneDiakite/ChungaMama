import uuid
import httpx
from fastapi import APIRouter, Depends, HTTPException
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
    messages: list[AssistantMessage]


# This router is intentionally thin: ChungaMama owns patient records and
# auth; Mane's conversational service (ASR/NLU/RAG) owns everything about
# understanding and responding to the message. This keeps his thesis
# artifact independently deployable and separately attributable, per the
# API contract agreed on: {patient_context, message} -> {intent, entities,
# risk_level, reply, escalate}.
@router.post("/chat")
async def chat(payload: AssistantRequest, db: Session = Depends(get_db)):
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            resp = await client.post(
                settings.ASSISTANT_SERVICE_URL,
                json={"messages": [m.model_dump() for m in payload.messages]},
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
