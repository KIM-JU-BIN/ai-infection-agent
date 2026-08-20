"""
위험도 평가 스키마
"""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from app.schemas.sop_document import SopSourceType


class RiskLevel(StrEnum):
    """
    위험도 등급
    """

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class AssessmentRequest(BaseModel):
    """
    접촉자 위험도 평가 요청
    """

    disease_type: str = Field(
        min_length=1,
        max_length=100,
        description="감염병 유형",
    )

    start_time: datetime = Field(
        description="접촉 추적 시작 시각",
    )

    end_time: datetime = Field(
        description="접촉 추적 종료 시각",
    )

    time_window_minutes: int = Field(
        default=30,
        ge=1,
        le=1440,
        description="접촉 추정 시간 범위",
    )

    distance_threshold: float | None = Field(
        default=None,
        gt=0,
        description="좌표 기반 거리 임계값",
    )

    source_type: SopSourceType | None = Field(
        default=None,
        description="SOP 출처 필터",
    )

    authority: str | None = Field(
        default=None,
        max_length=100,
        description="기관 필터",
    )

    top_k: int = Field(
        default=5,
        ge=1,
        le=10,
        description="검색할 SOP 문서 수",
    )


class ContactRiskItem(BaseModel):
    """
    접촉자별 위험도 결과
    """

    contact_id: int = Field(
        description="접촉자 환자 ID",
    )

    contact_identifier: str = Field(
        description="접촉자 환자 식별자",
    )

    contact_name: str = Field(
        description="접촉자 이름",
    )

    risk_level: RiskLevel = Field(
        description="위험도",
    )

    reason: str = Field(
        description="판정 근거",
    )

    action_plan: str = Field(
        description="조치 계획",
    )


class AssessmentSource(BaseModel):
    """
    위험도 평가에 사용한 SOP 출처
    """

    document_id: int = Field(description="문서 ID")
    document_code: str = Field(description="문서 코드")
    title: str = Field(description="문서 제목")
    source_type: str = Field(description="출처 유형")
    authority: str | None = Field(default=None, description="기관")
    disease_type: str | None = Field(default=None, description="감염병 유형")
    section: str | None = Field(default=None, description="섹션")
    chunk_index: int = Field(description="청크 순번")
    source_path: str | None = Field(default=None, description="원본 경로")
    distance: float = Field(description="검색 거리")


class AssessmentResponse(BaseModel):
    """
    위험도 평가 응답
    """

    index_patient_id: int = Field(description="기준 환자 ID")
    index_patient_identifier: str = Field(description="기준 환자 식별자")
    index_patient_name: str = Field(description="기준 환자명")
    disease_type: str = Field(description="감염병 유형")
    assessed_contact_count: int = Field(description="평가된 접촉자 수")
    risks: list[ContactRiskItem] = Field(description="접촉자별 위험도")
    sources: list[AssessmentSource] = Field(description="참고 SOP 문서")
