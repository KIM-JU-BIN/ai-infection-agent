"""
병상 배정 ORM 모델
동시간대 재실 여부 판단에 사용한다
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


if TYPE_CHECKING:
    from app.db.models.location import Location
    from app.db.models.patient import Patient


class BedAssignment(Base):
    """
    환자 병상 배정 정보
    """

    __tablename__ = "bed_assignments"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
        comment="병상 배정 PK",
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
        comment="병실 위치 ID",
    )

    admitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        comment="입실 시각",
    )

    discharged_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        comment="퇴실 시각",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="생성 시각",
    )

    patient: Mapped["Patient"] = relationship(
        back_populates="bed_assignments",
    )

    location: Mapped["Location"] = relationship(
        back_populates="bed_assignments",
    )

    __table_args__ = (
        Index(
            "ix_bed_assignments_patient_period",
            "patient_id",
            "admitted_at",
            "discharged_at",
        ),
        Index(
            "ix_bed_assignments_location_period",
            "location_id",
            "admitted_at",
            "discharged_at",
        ),
    )
