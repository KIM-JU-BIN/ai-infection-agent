"""
대시보드 응답 스키마
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DashboardCaseRead(BaseModel):
    """
    대시보드 접촉자 케이스 목록 응답
    """

    model_config = ConfigDict(from_attributes=True)

    case_id: int = Field(description="케이스 ID")
    index_patient_id: int = Field(description="기준 확진자 ID")
    patient_id: int = Field(description="접촉자 환자 ID")
    patient_identifier: str | None = Field(default=None, description="접촉자 환자번호")
    patient_name: str | None = Field(default=None, description="접촉자 이름")
    disease_type: str = Field(description="감염병 유형")
    contact_type: str | None = Field(default=None, description="접촉 유형")
    risk_level: str = Field(description="위험도")
    test_status: str = Field(description="검사 상태")
    sms_sent_status: str = Field(description="문자 발송 상태")
    monitoring_status: str = Field(description="모니터링 상태")
    case_status: str = Field(description="케이스 상태")
    reason: str | None = Field(default=None, description="AI 판정 근거")
    action_plan: str | None = Field(default=None, description="권장 조치")
    first_exposed_at: datetime | None = Field(default=None, description="최초 노출 시각")
    last_exposed_at: datetime | None = Field(default=None, description="마지막 노출 시각")
    created_at: datetime = Field(description="생성 시각")
    updated_at: datetime = Field(description="수정 시각")


class VitalSignRead(BaseModel):
    """"
    체온 기록 응답
    """

    id: int = Field(description="활력징후 ID")
    recorded_at: datetime = Field(description="측정 시각")
    temperature: float = Field(description="체온")
    source_system: str = Field(description="기록 출처")
    note: str | None = Field(default=None, description="메모")


class RecentAccessLogRead(BaseModel):
    """
    최근 출입 로그 응답
    """

    id: int = Field(description="출입 로그 ID")
    location_id: int = Field(description="위치 ID")
    location_name: str | None = Field(default=None, description="위치명")
    location_type: str | None = Field(default=None, description="위치 유형")
    floor: str | None = Field(default=None, description="층")
    occurred_at: datetime = Field(description="출입 시각")
    direction: str | None = Field(default=None, description="출입 방향")
    event_type: str = Field(description="이벤트 유형")


class PatientBasicInfo(BaseModel):
    """
    환자 기본 정보
    """

    id: int = Field(description="환자 ID")
    patient_identifier: str = Field(description="환자번호")
    name: str = Field(description="환자명")
    age: int | None = Field(default=None, description="나이")
    sex: str | None = Field(default=None, description="성별")
    current_diagnosis: str | None = Field(default=None, description="현재 진단명")
    phone_number: str | None = Field(default=None, description="연락처")
    address: str | None = Field(default=None, description="주소")


class PatientEMRDetail(BaseModel):
    """
    환자 EMR 상세 대시보드 응답
    """

    patient: PatientBasicInfo = Field(description="환자 기본 정보")
    latest_temperature: float | None = Field(default=None, description="최근 체온")
    latest_temperature_recorded_at: datetime | None = Field(
        default=None,
        description="최근 체온 측정 시각",
    )
    has_fever: bool = Field(description="발열 여부")
    vital_signs: list[VitalSignRead] = Field(description="체온 기록")
    recent_access_logs: list[RecentAccessLogRead] = Field(description="최근 동선")
