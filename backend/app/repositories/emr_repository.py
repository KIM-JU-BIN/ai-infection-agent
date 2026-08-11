from sqlalchemy.orm import Session

from app.models.emr_record import EMRRecord


class EMRRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_emr_by_patient(self, patient_id: str):
        return (
            self.db.query(EMRRecord)
            .filter(EMRRecord.patient_id == patient_id)
            .order_by(EMRRecord.created_at.desc())
            .all()
        )