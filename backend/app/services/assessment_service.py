"""
접촉자 위험도 평가 Service
접촉자 탐색 + SOP 검색 + LLM JSON 판정 + ContactCase 저장을 담당한다
"""

import json
from typing import Any

from openai import AsyncOpenAI
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AppError
from app.core.logging import get_logger
from app.db.models.post_action import ContactCase
from app.repositories.sop_repository import SopRepository
from app.llm.embedding_client import EmbeddingClient
from app.schemas.assessment import (
    AssessmentRequest,
    AssessmentResponse,
    AssessmentSource,
    ContactRiskItem,
)
from app.services.contact_tracing_service import ContactTracingService
from app.services.patient_service import PatientService


logger = get_logger(__name__)


class AssessmentService:
    """
    접촉자 위험도 평가 비즈니스 계층
    """

    def __init__(self, db: AsyncSession) -> None:
        """
        Service 초기화
        """

        if not settings.OPENAI_API_KEY:
            raise AppError(
                "OPENAI_API_KEY가 설정되지 않았습니다.",
                error_code="OPENAI_CONFIG_ERROR",
                status_code=500,
            )

        self.db = db
        self.patient_service = PatientService(db)
        self.contact_service = ContactTracingService(db)
        self.sop_repository = SopRepository(db)
        self.embedding_client = EmbeddingClient()
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    async def assess_contacts(
        self,
        *,
        patient_id: int,
        request: AssessmentRequest,
    ) -> AssessmentResponse:
        """
        기준 환자의 접촉자 위험도 평가
        """

        index_patient = await self.patient_service.get_patient(patient_id)

        contacts = await self.contact_service.find_contact_candidates(
            index_patient_id=patient_id,
            start_time=request.start_time,
            end_time=request.end_time,
            time_window_minutes=request.time_window_minutes,
            distance_threshold=request.distance_threshold,
        )

        if not contacts:
            return AssessmentResponse(
                index_patient_id=index_patient.id,
                index_patient_identifier=index_patient.patient_identifier,
                index_patient_name=index_patient.name,
                disease_type=request.disease_type,
                assessed_contact_count=0,
                risks=[],
                sources=[],
            )

        query_text = self._build_sop_search_query(request.disease_type)
        query_embedding = await self.embedding_client.embed_text(query_text)

        sop_rows = await self.sop_repository.search_by_vector(
            query_embedding=query_embedding,
            top_k=request.top_k,
            source_type=request.source_type.value if request.source_type else None,
            authority=request.authority,
            disease_type=request.disease_type,
        )

        sources = [
            AssessmentSource(
                document_id=document.id,
                document_code=document.document_code,
                title=document.title,
                source_type=document.source_type,
                authority=document.authority,
                disease_type=document.disease_type,
                section=document.section,
                chunk_index=document.chunk_index,
                source_path=document.source_path,
                distance=distance,
            )
            for document, distance in sop_rows
        ]

        if not sop_rows:
            risks = [
                ContactRiskItem(
                    contact_id=contact.patient_id,
                    contact_identifier=contact.patient_identifier,
                    contact_name=contact.patient_name,
                    risk_level="LOW",
                    reason=(
                        "관련 SOP 근거 문서를 찾지 못해 자동 위험도 판정이 제한됩니다. "
                        "감염관리 담당자 검토가 필요합니다."
                    ),
                    action_plan="추가 지침 확인 후 수동 검토를 진행하세요.",
                )
                for contact in contacts
            ]

            await self._save_contact_cases(
                index_patient_id=index_patient.id,
                disease_type=request.disease_type,
                contacts=contacts,
                risks=risks,
            )

            return AssessmentResponse(
                index_patient_id=index_patient.id,
                index_patient_identifier=index_patient.patient_identifier,
                index_patient_name=index_patient.name,
                disease_type=request.disease_type,
                assessed_contact_count=len(risks),
                risks=risks,
                sources=[],
            )

        context = self._build_context(sop_rows)
        contacts_payload = self._build_contacts_payload(contacts)

        risks = await self._generate_structured_risk_assessment(
            disease_type=request.disease_type,
            index_patient_id=index_patient.id,
            contacts_payload=contacts_payload,
            context=context,
        )

        await self._save_contact_cases(
            index_patient_id=index_patient.id,
            disease_type=request.disease_type,
            contacts=contacts,
            risks=risks,
        )

        return AssessmentResponse(
            index_patient_id=index_patient.id,
            index_patient_identifier=index_patient.patient_identifier,
            index_patient_name=index_patient.name,
            disease_type=request.disease_type,
            assessed_contact_count=len(risks),
            risks=risks,
            sources=sources,
        )

    async def _generate_structured_risk_assessment(
        self,
        *,
        disease_type: str,
        index_patient_id: int,
        contacts_payload: list[dict[str, Any]],
        context: str,
    ) -> list[ContactRiskItem]:
        """
        LLM으로 접촉자별 위험도 JSON 생성
        """

        try:
            response = await self.client.chat.completions.create(
                model=settings.CHAT_MODEL,
                temperature=0.1,
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "contact_risk_assessment",
                        "strict": True,
                        "schema": {
                            "type": "object",
                            "additionalProperties": False,
                            "properties": {
                                "risks": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "additionalProperties": False,
                                        "properties": {
                                            "contact_id": {
                                                "type": "integer",
                                                "description": "접촉자 환자 ID",
                                            },
                                            "contact_identifier": {
                                                "type": "string",
                                                "description": "접촉자 환자 식별자",
                                            },
                                            "contact_name": {
                                                "type": "string",
                                                "description": "접촉자 이름",
                                            },
                                            "risk_level": {
                                                "type": "string",
                                                "enum": ["HIGH", "MEDIUM", "LOW"],
                                                "description": "위험도",
                                            },
                                            "reason": {
                                                "type": "string",
                                                "description": "판정 근거",
                                            },
                                            "action_plan": {
                                                "type": "string",
                                                "description": "조치 계획",
                                            },
                                        },
                                        "required": [
                                            "contact_id",
                                            "contact_identifier",
                                            "contact_name",
                                            "risk_level",
                                            "reason",
                                            "action_plan",
                                        ],
                                    },
                                },
                            },
                            "required": ["risks"],
                        },
                    },
                },
                messages=[
                    {
                        "role": "system",
                        "content": self._build_system_prompt(),
                    },
                    {
                        "role": "user",
                        "content": self._build_user_prompt(
                            disease_type=disease_type,
                            index_patient_id=index_patient_id,
                            contacts_payload=contacts_payload,
                            context=context,
                        ),
                    },
                ],
            )

            content = response.choices[0].message.content

            if not content:
                raise AppError(
                    "LLM 위험도 평가 응답이 비어 있습니다.",
                    error_code="EMPTY_ASSESSMENT_RESPONSE",
                    status_code=502,
                )

            parsed = json.loads(content)
            risks_raw = parsed.get("risks", [])

            return [ContactRiskItem.model_validate(item) for item in risks_raw]

        except ValidationError as exc:
            logger.exception("LLM 위험도 JSON 검증 실패.")
            raise AppError(
                "LLM 위험도 평가 JSON 형식이 올바르지 않습니다.",
                error_code="ASSESSMENT_JSON_VALIDATION_ERROR",
                status_code=502,
            ) from exc

        except json.JSONDecodeError as exc:
            logger.exception("LLM 위험도 JSON 파싱 실패.")
            raise AppError(
                "LLM 위험도 평가 JSON 파싱에 실패했습니다.",
                error_code="ASSESSMENT_JSON_PARSE_ERROR",
                status_code=502,
            ) from exc

        except AppError:
            raise

        except Exception as exc:
            logger.exception("LLM 위험도 평가 실패.")
            raise AppError(
                "접촉자 위험도 평가 생성에 실패했습니다.",
                error_code="ASSESSMENT_GENERATION_ERROR",
                status_code=502,
            ) from exc

    async def _save_contact_cases(
        self,
        *,
        index_patient_id: int,
        disease_type: str,
        contacts: list[Any],
        risks: list[ContactRiskItem],
    ) -> None:
        """
        AI 위험도 평가 결과를 ContactCase로 저장
        """

        contact_map = {contact.patient_id: contact for contact in contacts}

        cases: list[ContactCase] = []

        for risk in risks:
            contact = contact_map.get(risk.contact_id)

            if contact is None:
                continue

            risk_level = (
                risk.risk_level.value
                if hasattr(risk.risk_level, "value")
                else str(risk.risk_level)
            )

            cases.append(
                ContactCase(
                    index_patient_id=index_patient_id,
                    patient_id=risk.contact_id,
                    disease_type=disease_type,
                    contact_type=getattr(contact, "contact_type", None),
                    risk_level=risk_level,
                    test_status=self._decide_initial_test_status(
                        risk_level=risk_level,
                    ),
                    sms_sent_status=self._decide_initial_sms_status(
                        risk_level=risk_level,
                    ),
                    monitoring_status=self._decide_initial_monitoring_status(
                        risk_level=risk_level,
                    ),
                    case_status=self._decide_initial_case_status(
                        risk_level=risk_level,
                    ),
                    reason=risk.reason,
                    action_plan=risk.action_plan,
                    first_exposed_at=getattr(contact, "occurred_at", None),
                    last_exposed_at=getattr(contact, "occurred_at", None),
                )
            )

        if not cases:
            return

        self.db.add_all(cases)
        await self.db.flush()

    @staticmethod
    def _decide_initial_test_status(*, risk_level: str) -> str:
        """
        위험도별 초기 검사 상태
        """

        if risk_level in {"HIGH", "MEDIUM"}:
            return "RECOMMENDED"

        return "NOT_REQUIRED"

    @staticmethod
    def _decide_initial_sms_status(*, risk_level: str) -> str:
        """
        위험도별 초기 문자 상태
        """

        if risk_level in {"HIGH", "MEDIUM"}:
            return "PENDING"

        return "NOT_NEEDED"

    @staticmethod
    def _decide_initial_monitoring_status(*, risk_level: str) -> str:
        """
        위험도별 초기 모니터링 상태
        """

        if risk_level in {"HIGH", "MEDIUM", "LOW"}:
            return "ACTIVE"

        return "NOT_STARTED"

    @staticmethod
    def _decide_initial_case_status(*, risk_level: str) -> str:
        """
        위험도별 초기 케이스 상태
        """

        if risk_level == "HIGH":
            return "ACTION_REQUIRED"

        if risk_level == "MEDIUM":
            return "MONITORING"

        if risk_level == "LOW":
            return "MONITORING"

        return "OPEN"

    @staticmethod
    def _build_sop_search_query(disease_type: str) -> str:
        """
        SOP 검색 질문 생성
        """

        normalized_disease_type = disease_type.strip()

        if not normalized_disease_type:
            normalized_disease_type = "감염병"

        return (
            f"{normalized_disease_type} 의료기관 감염관리 접촉자 분류 기준 "
            "노출 시간 동일 병실 동시간대 체류 출입 로그 접촉자 위험도 평가 "
            "격리 검사 권고 모니터링 보호구 착용"
        )

    @staticmethod
    def _build_contacts_payload(contacts: list[Any]) -> list[dict[str, Any]]:
        """
        접촉자 정보를 LLM 입력용으로 변환
        """

        return [
            {
                "contact_id": contact.patient_id,
                "contact_identifier": contact.patient_identifier,
                "contact_name": contact.patient_name,
                "location_id": contact.location_id,
                "location_name": contact.location_name,
                "occurred_at": contact.occurred_at.isoformat(),
                "distance": contact.distance,
                "time_diff_minutes": contact.time_diff_minutes,
                "contact_type": getattr(contact, "contact_type", None),
            }
            for contact in contacts
        ]

    @staticmethod
    def _build_context(sop_rows: list[tuple[Any, float]]) -> str:
        """
        SOP 검색 결과를 Context로 변환
        """

        blocks: list[str] = []

        for index, (document, distance) in enumerate(sop_rows, start=1):
            blocks.append(
                f"""
[지침서 {index}]
문서ID: {document.id}
문서코드: {document.document_code}
제목: {document.title}
출처: {document.source_type}
기관: {document.authority or "N/A"}
감염병: {document.disease_type or "N/A"}
섹션: {document.section or "N/A"}
청크: {document.chunk_index}
검색거리: {distance}
본문:
{document.content}
""".strip()
            )

        return "\n\n---\n\n".join(blocks)

    @staticmethod
    def _build_system_prompt() -> str:
        """
        위험도 평가 시스템 프롬프트
        """

        return """
너는 전문적인 병원 감염관리 위험도 평가 AI 에이전트다.

반드시 아래 규칙을 지켜라.

1. 제공된 SOP Context에 근거해서만 판단한다.
2. Context에 없는 내용은 추측하지 않는다.
3. 접촉 시간, 같은 위치 여부, 거리, 지침서 근거를 함께 고려한다.
4. 위험도는 반드시 HIGH, MEDIUM, LOW 중 하나만 사용한다.
5. 의학적 최종 확정 판단이 아니라 감염관리 담당자 검토용 초안으로 작성한다.
6. 환자 개인정보를 불필요하게 반복하지 않는다.
7. 응답은 반드시 지정된 JSON Schema만 따른다.
8. reason과 action_plan은 한국어로 작성한다.
""".strip()

    @staticmethod
    def _build_user_prompt(
        *,
        disease_type: str,
        index_patient_id: int,
        contacts_payload: list[dict[str, Any]],
        context: str,
    ) -> str:
        """
        위험도 평가 사용자 프롬프트
        """

        return f"""
[감염병 유형]
{disease_type}

[기준 환자 ID]
{index_patient_id}

[접촉자 목록]
{json.dumps(contacts_payload, ensure_ascii=False, indent=2)}

[SOP Context]
{context}

[판정 기준]
[판정 기준]
- 위험도는 HIGH, MEDIUM, LOW 중 하나만 선택한다.
- HIGH는 같은 병실 장시간 동시 재실, 동일 처치실 동시간대 출입, 또는 BED_ASSIGNMENT_OVERLAP+ACCESS_LOG_OVERLAP처럼 강한 접촉 근거가 있을 때 사용한다.
- MEDIUM은 직접적인 강한 접촉은 부족하지만 무시할 수 없는 노출 가능성이 있을 때 사용한다.
- MEDIUM 예시 1: 같은 병실 재실 기록은 있으나 겹친 시간이 짧거나 입실/퇴실 경계 시간이 애매한 경우.
- MEDIUM 예시 2: 같은 층 또는 같은 병동의 공용 공간을 비슷한 시간대에 사용했지만 동일한 방/처치실이 직접 겹치지는 않는 경우.
- MEDIUM 예시 3: 같은 장소 출입 기록은 있으나 시간 차이가 15~30분 정도로 동시 체류가 확실하지 않은 경우.
- MEDIUM 예시 4: 접촉 강도는 낮지만 고령, 폐질환, 면역저하, 발열 경계 체온 등 취약 요인이 있는 경우.
- MEDIUM 예시 5: 보호구 착용 여부나 검사 여부가 불명확하여 LOW로 낮추기 어려운 경우.
- LOW는 접촉 근거가 약하고 시간/공간 겹침이 거의 없으며 추가 위험 신호가 없을 때만 사용한다.
- 같은 위치에서 시간 차이가 작을수록 위험도가 높다.
- 거리 정보가 있으면 가까울수록 위험도가 높다.
- 같은 병실 재실 접촉은 중요한 위험 근거로 본다.
- BED_ASSIGNMENT_OVERLAP은 병실 동시 체류 근거다.
- ACCESS_LOG_OVERLAP은 출입 로그 기반 동선 겹침 근거다.
- BED_ASSIGNMENT_OVERLAP+ACCESS_LOG_OVERLAP은 병실과 동선이 모두 겹친 강한 근거다.
- SOP Context의 접촉자 분류, 격리, 검사, 보호구 관련 내용을 우선 적용한다.
- 근거가 부족하면 LOW로 단정하지 말고 reason에 "근거 부족"을 명시한다.
- 각 접촉자마다 contact_id, contact_identifier, contact_name, risk_level, reason, action_plan을 반드시 작성한다.
""".strip()

