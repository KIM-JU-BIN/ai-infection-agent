from sqlalchemy.orm import Session

from app.models.patient import Patient


class PatientRepository:

    def __init__(self, db: Session):
        self.db = db
        
    # 환자 한 명 조회
    def get_patient(self, patient_id: str):
        return (
            self.db.query(Patient)
            .filter(Patient.patient_id == patient_id)
            .first()
        )
    
    # 전체 환자 조회
    def get_all_patients(self):
        return self.db.query(Patient).all()

    