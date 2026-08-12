"""
의무기록 ORM 모델
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


if TYPE_CHECKING:
    from app.db.models.patient import Patient


class EmrRecord(Base):
    """
    환자 EMR 기록
    """

    __tablename__ = "emr_records"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
        comment="EMR PK",
    )

    patient_id: Mapped[int] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="환자 ID",
    )

    record_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="기록 유형",
    )

    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        comment="기록 시각",
    )

    department: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="진료과",
    )

    diagnosis_code: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        index=True,
        comment="진단 코드",
    )

    title: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        comment="기록 제목",
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="기록 본문",
    )

    structured_data: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="구조화 EMR 데이터",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="생성 시각",
    )

    patient: Mapped["Patient"] = relationship(
        back_populates="emr_records",
    )

    __table_args__ = (
        Index(
            "ix_emr_records_patient_recorded_at",
            "patient_id",
            "recorded_at",
        ),
        Index(
            "ix_emr_records_structured_data_gin",
            "structured_data",
            postgresql_using="gin",
        ),
    )
