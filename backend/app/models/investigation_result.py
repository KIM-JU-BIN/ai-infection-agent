from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey

from app.database.db import Base


class InvestigationResult(Base):
    __tablename__ = "investigation_results"

    result_id = Column(Integer, primary_key=True, autoincrement=True)

    patient_id = Column(
        String(20),
        ForeignKey("patients.patient_id"),
        nullable=False
    )

    risk_level = Column(
        String(20),
        nullable=False
    )

    evidence = Column(
        Text,
        nullable=False
    )

    ai_reasoning = Column(
        Text,
        nullable=False
    )

    status = Column(
        String(30),
        nullable=False
    )

    created_at = Column(
        DateTime,
        nullable=False
    )