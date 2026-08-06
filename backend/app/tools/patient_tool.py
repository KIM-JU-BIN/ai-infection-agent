from app.database.db import SessionLocal
from app.repositories.patient_repository import PatientRepository


def get_patient_info(patient_id: str):
    """
    환자 1명의 정보를 조회한다.
    """

    db = SessionLocal()

    try:
        repository = PatientRepository(db)

        patient = repository.get_patient(patient_id)

        if patient is None:
            return {
                "success": False,
                "message": "환자를 찾을 수 없습니다."
            }

        return {
            "success": True,
            "patient_id": patient.patient_id,
            "name": patient.name,
            "admission_date": str(patient.admission_date),
            "diagnosis": patient.diagnosis,
            "current_location_id": patient.current_location_id
        }

    finally:
        db.close()