"""
출입 로그 스키마
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.location import LocationRead
from app.schemas.patient import PatientRead


class AccessLogBase(BaseModel):
    """
    출입 로그 공통 필드
    """

    patient_id: int = Field(
        gt=0,
        description="환자 ID",
    )
    location_id: int = Field(
        gt=0,
        description="위치 ID",
    )
    occurred_at: datetime = Field(
        description="출입 발생 시각",
    )
    event_type: str = Field(
        min_length=1,
        max_length=30,
        description="이벤트 유형",
    )
    source_system: str | None = Field(
        default=None,
        max_length=100,
        description="원천 시스템",
    )
    raw_payload: str | None = Field(
        default=None,
        description="원본 로그",
    )


class AccessLogCreate(AccessLogBase):
    """
    출입 로그 생성 요청
    """

    pass


class AccessLogRead(AccessLogBase):
    """
    출입 로그 응답.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="출입 로그 PK")
    created_at: datetime = Field(description="생성 시각")


class AccessLogWithRelations(AccessLogRead):
    """
    환자/위치 포함 출입 로그 응답
    """

    patient: PatientRead = Field(description="환자 정보")
    location: LocationRead = Field(description="위치 정보")


class ContactCandidate(BaseModel):
    """
    접촉 후보자
    """

    patient_id: int = Field(description="접촉 후보 환자 ID")
    patient_identifier: str = Field(description="접촉 후보 환자 식별자")
    patient_name: str = Field(description="접촉 후보 환자명")
    location_id: int = Field(description="공통 위치 ID")
    location_name: str = Field(description="공통 위치명")
    occurred_at: datetime = Field(description="접촉 추정 시각")
    distance: float | None = Field(default=None, description="좌표 기반 거리")
    time_diff_minutes: float = Field(description="기준 환자와의 시간 차이")
    contact_type: str = Field(description="접촉 유형")
