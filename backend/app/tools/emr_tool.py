from app.database.db import SessionLocal
from app.repositories.emr_repository import EMRRepository


def get_patient_emr(patient_id: str):
    """
    특정 환자의 EMR 기록 조회
    """

    db = SessionLocal()

    try:
        repository = EMRRepository(db)

        records = repository.get_emr_by_patient(patient_id)

        if not records:
            return {
                "success": False,
                "message": "EMR 기록이 없습니다."
            }

        result = []

        for record in records:
            result.append({
                "record_id": record.record_id,
                "record_type": record.record_type,
                "note_text": record.note_text,
                "created_at": str(record.created_at)
            })

        return {
            "success": True,
            "patient_id": patient_id,
            "records": result
        }

    finally:
        db.close()