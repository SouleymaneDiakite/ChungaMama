import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class UserCreate(BaseModel):
    full_name: str | None = None
    email: str | None = None
    phone: str | None = None
    password: str
    role: str = "mother"  # DEV-ONLY: open role selection at register is fine
    # for testing CHW/admin views locally, but must be gated (admin-invite
    # only, or a separate staff-provisioning flow) before any real deployment.


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    full_name: str | None
    email: str | None
    phone: str | None
    role: str
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ForgotPasswordRequest(BaseModel):
    email: str | None = None
    phone: str | None = None


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str
