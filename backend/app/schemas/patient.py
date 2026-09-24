import uuid
from datetime import date, datetime
from pydantic import BaseModel, ConfigDict, Field


class PatientCreate(BaseModel):
    full_name: str = Field(validation_alias="name", serialization_alias="full_name")
    estimated_due_date: date | None = None

    model_config = ConfigDict(populate_by_name=True)


class PatientOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    full_name: str
    estimated_due_date: date | None
    risk_level: str
    created_at: datetime
