"""
환자 ORM 모델
"""

from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, String, Text, func, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


if TYPE_CHECKING:
    from app.db.models.access_log import AccessLog
    from app.db.models.emr_record import EmrRecord
    from app.db.models.bed_assignment import BedAssignment
    from app.db.models.investigation_result import InvestigationResult


class Patient(Base):
    """
    환자 정보
    """

    __tablename__ = "patients"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
        comment="내부 환자 PK",
    )

    patient_identifier: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        index=True,
        nullable=False,
        comment="병원 환자 식별자",
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="환자명",
    )
    
    age: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="나이",
    )

    birth_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment="생년월일",
    )

    sex: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="성별",
    )

    phone_number: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
        comment="연락처",
    )

    address: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="주소",
    )
    
    current_diagnosis: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        comment="현재 진단명",
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

    access_logs: Mapped[list["AccessLog"]] = relationship(
        back_populates="patient",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    
    bed_assignments: Mapped[list["BedAssignment"]] = relationship(
        back_populates="patient",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    emr_records: Mapped[list["EmrRecord"]] = relationship(
        back_populates="patient",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    investigation_results: Mapped[list["InvestigationResult"]] = relationship(
        back_populates="patient",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
