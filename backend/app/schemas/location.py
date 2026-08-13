"""
위치 스키마
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class LocationBase(BaseModel):
    """
    위치 공통 필드
    """

    location_code: str = Field(
        min_length=1,
        max_length=64,
        description="위치 코드",
    )
    name: str = Field(
        min_length=1,
        max_length=150,
        description="위치명",
    )
    location_type: str = Field(
        min_length=1,
        max_length=50,
        description="위치 유형",
    )
    floor: str | None = Field(
        default=None,
        max_length=30,
        description="층",
    )
    building: str | None = Field(
        default=None,
        max_length=100,
        description="건물명",
    )
    description: str | None = Field(
        default=None,
        description="설명",
    )
    x_coord: float | None = Field(
        default=None,
        description="X 좌표",
    )
    y_coord: float | None = Field(
        default=None,
        description="Y 좌표",
    )


class LocationRead(LocationBase):
    """
    위치 응답
    """

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="위치 PK")
    parent_id: int | None = Field(default=None, description="상위 위치 ID")
    created_at: datetime = Field(description="생성 시각")
    updated_at: datetime = Field(description="수정 시각")
