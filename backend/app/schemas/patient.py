"""
환자 스키마
"""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class PatientBase(BaseModel):
    """
    환자 공통 필드
    """

    patient_identifier: str = Field(
        min_length=1,
        max_length=64,
        description="병원 환자 식별자",
    )
    name: str = Field(
        min_length=1,
        max_length=100,
        description="환자명",
    )
    birth_date: date | None = Field(
        default=None,
        description="생년월일",
    )
    sex: str | None = Field(
        default=None,
        max_length=20,
        description="성별",
    )
    phone_number: str | None = Field(
        default=None,
        max_length=30,
        description="연락처",
    )
    address: str | None = Field(
        default=None,
        description="주소",
    )


class PatientCreate(PatientBase):
    """
    환자 생성 요청
    """

    pass


class PatientUpdate(BaseModel):
    """
    환자 수정 요청
    """

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="환자명",
    )
    birth_date: date | None = Field(
        default=None,
        description="생년월일",
    )
    sex: str | None = Field(
        default=None,
        max_length=20,
        description="성별",
    )
    phone_number: str | None = Field(
        default=None,
        max_length=30,
        description="연락처",
    )
    address: str | None = Field(
        default=None,
        description="주소",
    )


class PatientRead(PatientBase):
    """
    환자 응답
    """

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="환자 PK")
    created_at: datetime = Field(description="생성 시각")
    updated_at: datetime = Field(description="수정 시각")
