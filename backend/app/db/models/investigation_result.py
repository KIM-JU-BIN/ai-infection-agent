"""
조사 결과 ORM 모델
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


if TYPE_CHECKING:
    from app.db.models.patient import Patient


class InvestigationResult(Base):
    """
    감염관리 조사 결과
    """

    __tablename__ = "investigation_results"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
        comment="조사 결과 PK",
    )

    patient_id: Mapped[int] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="기준 환자 ID",
    )

    investigation_uid: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=False,
        comment="조사 고유 ID",
    )

    disease_type: Mapped[str] = mapped_column(
        String(100),
        index=True,
        nullable=False,
        comment="감염병 유형",
    )

    status: Mapped[str] = mapped_column(
        String(30),
        index=True,
        nullable=False,
        comment="조사 상태",
    )

    risk_level: Mapped[str | None] = mapped_column(
        String(30),
        index=True,
        nullable=True,
        comment="최종 위험도",
    )

    summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="조사 요약",
    )

    result_json: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        comment="FHIR 참고 구조화 조사 결과",
    )

    evidence_json: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="근거 문서 및 판단 근거",
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="오류 메시지",
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

    patient: Mapped["Patient"] = relationship(
        back_populates="investigation_results",
    )

    __table_args__ = (
        Index(
            "ix_investigation_results_patient_created",
            "patient_id",
            "created_at",
        ),
        Index(
            "ix_investigation_results_result_json_gin",
            "result_json",
            postgresql_using="gin",
        ),
        Index(
            "ix_investigation_results_evidence_json_gin",
            "evidence_json",
            postgresql_using="gin",
        ),
    )
