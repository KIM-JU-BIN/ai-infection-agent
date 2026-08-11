from sqlalchemy.orm import Session

from app.models.access_log import AccessLog


class AccessRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_access_logs_by_patient(self, patient_id: str):
        return (
            self.db.query(AccessLog)
            .filter(AccessLog.patient_id == patient_id)
            .order_by(AccessLog.enter_time.desc())
            .all()
        )