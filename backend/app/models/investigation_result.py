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

    # 예: Low, Medium, High
    risk_level = Column(
        String(20),
        nullable=False
    )

    # 매우 중요
    # 판단 근거를 저장함
    evidence = Column(
        Text,
        nullable=False
    )

    # LLM이 생성한 최종 설명이 저장됨
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