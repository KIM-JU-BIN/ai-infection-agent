"""
사후 관리 ORM 모델

ContactCase:
- AI 위험도 평가 결과를 저장한다.
- 접촉자별 검사/문자/관리 상태를 추적한다.

VitalSign:
- 환자 체온을 지속적으로 저장한다.

LabTest:
- 감염병 검사 여부와 결과를 저장한다.
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


if TYPE_CHECKING:
    from app.db.models.patient import Patient


class ContactCase(Base):
    """
    접촉자 사후 관리 케이스
    """

    __tablename__ = "contact_cases"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
        comment="접촉자 케이스 PK",
    )

    index_patient_id: Mapped[int] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="기준 확진자 ID",
    )

    patient_id: Mapped[int] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="접촉자 환자 ID",
    )

    disease_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="감염병 유형",
    )

    contact_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        comment="접촉 유형",
    )

    risk_level: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        comment="위험도 HIGH/MEDIUM/LOW",
    )

    test_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="RECOMMENDED",
        server_default="RECOMMENDED",
        index=True,
        comment="검사 상태",
    )

    sms_sent_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="PENDING",
        server_default="PENDING",
        index=True,
        comment="문자 발송 상태",
    )

    monitoring_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="ACTIVE",
        server_default="ACTIVE",
        index=True,
        comment="모니터링 상태",
    )

    case_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="OPEN",
        server_default="OPEN",
        index=True,
        comment="케이스 상태",
    )

    reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="AI 위험도 판정 근거",
    )

    action_plan: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="권장 조치",
    )

    first_exposed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        comment="최초 노출 시각",
    )

    last_exposed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        comment="마지막 노출 시각",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="생성 시각",
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="수정 시각",
    )

    index_patient: Mapped["Patient"] = relationship(
        foreign_keys=[index_patient_id],
    )

    patient: Mapped["Patient"] = relationship(
        foreign_keys=[patient_id],
    )

    __table_args__ = (
        Index(
            "ix_contact_cases_index_patient_contact",
            "index_patient_id",
            "patient_id",
        ),
        Index(
            "ix_contact_cases_risk_test_sms",
            "risk_level",
            "test_status",
            "sms_sent_status",
        ),
        Index(
            "ix_contact_cases_case_monitoring",
            "case_status",
            "monitoring_status",
        ),
    )


class VitalSign(Base):
    """
    환자 활력징후
    현재는 체온 중심으로 추적한다
    """

    __tablename__ = "vital_signs"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
        comment="활력징후 PK",
    )

    patient_id: Mapped[int] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="환자 ID",
    )

    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        comment="측정 시각",
    )

    temperature: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="체온",
    )

    source_system: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="SYNTHETIC",
        server_default="SYNTHETIC",
        comment="기록 출처",
    )

    note: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="증상 메모",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="생성 시각",
    )

    patient: Mapped["Patient"] = relationship()

    __table_args__ = (
        Index(
            "ix_vital_signs_patient_recorded",
            "patient_id",
            "recorded_at",
        ),
        Index(
            "ix_vital_signs_temperature_recorded",
            "temperature",
            "recorded_at",
        ),
    )


class LabTest(Base):
    """
    감염병 검사 기록
    미검사자 추적과 자동 문자 발송 판단에 사용한다
    """

    __tablename__ = "lab_tests"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
        comment="검사 기록 PK",
    )

    patient_id: Mapped[int] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="환자 ID",
    )

    test_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        comment="검사 일시",
    )

    test_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="검사 유형 PCR/RAT 등",
    )

    disease_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="감염병 유형",
    )

    result: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        index=True,
        comment="검사 결과 PENDING/NEGATIVE/POSITIVE 등",
    )

    source_system: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="SYNTHETIC",
        server_default="SYNTHETIC",
        comment="검사 출처",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="생성 시각",
    )

    patient: Mapped["Patient"] = relationship()

    __table_args__ = (
        Index(
            "ix_lab_tests_patient_disease_date",
            "patient_id",
            "disease_type",
            "test_date",
        ),
        Index(
            "ix_lab_tests_patient_result",
            "patient_id",
            "result",
        ),
    )
