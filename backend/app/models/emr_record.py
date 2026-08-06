from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey

from app.database.db import Base


class EMRRecord(Base):
    __tablename__ = "emr_records"

    record_id = Column(Integer, primary_key=True, autoincrement=True)

    # 환자 한 명에서 EMR은 여러개가 존재할 수 있음
    patient_id = Column(
        String(20),
        ForeignKey("patients.patient_id"),
        nullable=False
    )

    # Agent가 어떤 종류의 기록인지 판단 가능
    # 예시: Doctor Note, Nurse Note, Operation Note, Medication
    record_type = Column(
        String(50),
        nullable=False
    )

    # 이게 가장 중요
    # AI가 읽는 데이터
    note_text = Column(
        Text,
        nullable=False
    )

    created_at = Column(
        DateTime,
        nullable=False
    )