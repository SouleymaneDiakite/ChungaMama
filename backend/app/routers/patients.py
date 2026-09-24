import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.patient import Patient
from app.schemas.patient import PatientCreate, PatientOut

router = APIRouter()


@router.post("", response_model=PatientOut)
def create_patient(payload: PatientCreate, db: Session = Depends(get_db)):
    patient = Patient(
        full_name=payload.full_name,
        estimated_due_date=payload.estimated_due_date,
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


@router.get("/{patient_id}", response_model=PatientOut)
def get_patient(patient_id: str, db: Session = Depends(get_db)):
    try:
        pid = uuid.UUID(patient_id)
    except ValueError:
        raise HTTPException(422, "Invalid patient id")

    patient = db.query(Patient).filter(Patient.id == pid).first()
    if not patient:
        raise HTTPException(404, "Patient not found")
    return patient


@router.get("", response_model=list[PatientOut])
def list_patients(db: Session = Depends(get_db)):
    return db.query(Patient).all()
