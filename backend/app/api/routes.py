from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.db import SessionLocal
from app.repositories.patient_repository import PatientRepository

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/patients")
def get_patients(db: Session = Depends(get_db)):
    repository = PatientRepository(db)
    return repository.get_all_patients()


@router.get("/patients/{patient_id}")
def get_patient(patient_id: str, db: Session = Depends(get_db)):
    repository = PatientRepository(db)
    return repository.get_patient(patient_id)