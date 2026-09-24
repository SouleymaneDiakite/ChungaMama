import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class EscalationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    patient_id: uuid.UUID | None
    intent: str | None
    risk_level: str
    summary: str
    reviewed: bool
    reviewed_at: datetime | None
    created_at: datetime


class EscalationReview(BaseModel):
    reviewed: bool = True
