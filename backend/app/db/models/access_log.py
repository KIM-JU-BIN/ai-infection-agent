"""
출입 로그 ORM 모델
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


if TYPE_CHECKING:
    from app.db.models.location import Location
    from app.db.models.patient import Patient


class AccessLog(Base):
    """
    환자 위치 이동/출입 기록
    """

    __tablename__ = "access_logs"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
        comment="출입 로그 PK",
    )

    patient_id: Mapped[int] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="환자 ID",
    )

    location_id: Mapped[int] = mapped_column(
        ForeignKey("locations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="위치 ID",
    )

    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        comment="출입 발생 시각",
    )

    event_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        comment="이벤트 유형",
    )

    source_system: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="원천 시스템",
    )

    raw_payload: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="원본 로그",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="생성 시각",
    )

    patient: Mapped["Patient"] = relationship(
        back_populates="access_logs",
    )

    location: Mapped["Location"] = relationship(
        back_populates="access_logs",
    )

    __table_args__ = (
        Index(
            "ix_access_logs_patient_time",
            "patient_id",
            "occurred_at",
        ),
        Index(
            "ix_access_logs_location_time",
            "location_id",
            "occurred_at",
        ),
        Index(
            "ix_access_logs_spacetime",
            "patient_id",
            "location_id",
            "occurred_at",
        ),
    )
