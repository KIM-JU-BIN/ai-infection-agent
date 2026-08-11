from app.database.db import SessionLocal
from app.repositories.access_repository import AccessRepository


def get_patient_access_logs(patient_id: str):
    """
    특정 환자의 출입기록 조회
    """

    db = SessionLocal()

    try:
        repository = AccessRepository(db)

        logs = repository.get_access_logs_by_patient(patient_id)

        if not logs:
            return {
                "success": False,
                "message": "출입기록이 없습니다."
            }

        result = []

        for log in logs:
            result.append({
                "log_id": log.log_id,
                "location_id": log.location_id,
                "enter_time": str(log.enter_time),
                "exit_time": (
                    str(log.exit_time)
                    if log.exit_time else None
                )
            })

        return {
            "success": True,
            "patient_id": patient_id,
            "logs": result
        }

    finally:
        db.close()