"""
병원 위치 ORM 모델
PostGIS 없이 x_coord, y_coord만 사용한다
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


if TYPE_CHECKING:
    from app.db.models.access_log import AccessLog
    from app.db.models.bed_assignment import BedAssignment


class Location(Base):
    """
    병원 내 위치/POI
    """

    __tablename__ = "locations"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
        comment="위치 PK",
    )

    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("locations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="상위 위치 ID",
    )

    location_code: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        index=True,
        nullable=False,
        comment="위치 코드",
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        comment="장소명",
    )

    location_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="위치 유형",
    )

    floor: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
        comment="층수",
    )

    building: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="건물명",
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="설명",
    )

    # PostGIS 대신 이 실수형 좌표 2개로 거리를 계산합니다.
    x_coord: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        comment="평면 X 좌표",
    )

    y_coord: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        comment="평면 Y 좌표",
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

    parent: Mapped["Location | None"] = relationship(
        remote_side=[id],
        back_populates="children",
    )

    children: Mapped[list["Location"]] = relationship(
        back_populates="parent",
    )

    access_logs: Mapped[list["AccessLog"]] = relationship(
        back_populates="location",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    
    bed_assignments: Mapped[list["BedAssignment"]] = relationship(
        back_populates="location",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    __table_args__ = (
        Index("ix_locations_type_floor", "location_type", "floor"),
        Index("ix_locations_xy", "x_coord", "y_coord"),
    )
