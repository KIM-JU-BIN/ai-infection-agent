from typing import Any, Literal, TypedDict


class InvestigationState(TypedDict, total=False):
    """
    LangGraph 감염 조사 워크플로우의 공유 상태.

    각 노드는 이 상태를 입력받아 필요한 값을 추가하거나 갱신합니다.
    """

    request_id: str
    patient_id: str
    disease_type: str
    index_time: str

    patient_profile: dict[str, Any]
    movement_logs: list[dict[str, Any]]
    contact_candidates: list[dict[str, Any]]

    retrieved_sops: list[dict[str, Any]]
    risk_assessments: list[dict[str, Any]]

    validation_status: Literal["passed", "failed", "needs_review"]
    validation_errors: list[str]

    final_report: dict[str, Any]
    error_message: str
