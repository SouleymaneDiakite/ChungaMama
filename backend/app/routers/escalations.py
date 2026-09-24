import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.escalation import Escalation
from app.models.user import User
from app.schemas.escalation import EscalationOut, EscalationReview
from app.services.security import require_staff

router = APIRouter()


@router.get("", response_model=list[EscalationOut])
def list_escalations(
    reviewed: bool | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(require_staff),
):
    query = db.query(Escalation)
    if reviewed is not None:
        query = query.filter(Escalation.reviewed == reviewed)
    return query.order_by(Escalation.created_at.desc()).all()


@router.post("/{escalation_id}/review", response_model=EscalationOut)
def review_escalation(
    escalation_id: str,
    payload: EscalationReview,
    db: Session = Depends(get_db),
    staff: User = Depends(require_staff),
):
    try:
        eid = uuid.UUID(escalation_id)
    except ValueError:
        raise HTTPException(422, "Invalid escalation id")

    escalation = db.query(Escalation).filter(Escalation.id == eid).first()
    if not escalation:
        raise HTTPException(404, "Escalation not found")

    escalation.reviewed = payload.reviewed
    escalation.reviewed_by = staff.id
    escalation.reviewed_at = datetime.utcnow() if payload.reviewed else None
    db.commit()
    db.refresh(escalation)
    return escalation
