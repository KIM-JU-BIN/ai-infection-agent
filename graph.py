from typing import TypedDict, Optional, Dict, Any
from langgraph.graph import StateGraph, END

# 1. 그래프 상태(State) 정의
class PipelineState(TypedDict):
    raw_text: str
    masked_text: Optional[str]
    standardized_text: Optional[str]
    fhir_json: Optional[Dict[str, Any]]
    validation_error: Optional[str]
    retry_count: int

# 2. 노드 함수 정의 (역할 중심 명명)
def mask_pii_data(state: PipelineState) -> PipelineState:
    """Step 1: 정규식 & Lookup Table 기반 PII/PHI 비식별화 (Deterministic Gate)"""
    # TODO: Regex 및 마스킹 로직 적용
    masked = state["raw_text"]  # 마스킹 처리 결과 예시
    return {"masked_text": masked}

def retrieve_medical_ontology(state: PipelineState) -> PipelineState:
    """Step 2: pgvector 실시간 유사도 검색 및 표준 의학 용어 맵핑 (Medical RAG)"""
    # TODO: PostgreSQL pgvector 조회 및 용어 변환
    standardized = state["masked_text"]  # 용어 맵핑 결과 예시
    return {"standardized_text": standardized}

def map_to_fhir_schema(state: PipelineState) -> PipelineState:
    """Step 3: Local sLLM을 이용한 FHIR R4 JSON 추론 (FHIR Mapper)"""
    error_prompt = state.get("validation_error")
    
    if error_prompt:
        # Retry 시: Error Refinement Prompt 추가하여 재추론
        # prompt = f"이전 생성 JSON에서 오류가 발생했습니다: {error_prompt}. 수정해주세요."
        pass
    else:
        # 최초 추론 시
        pass
        
    # TODO: sLLM 호출 (JSON Mode / Function Calling)
    inferred_json = {}  # LLM 추론 결과 예시
    return {"fhir_json": inferred_json}

def validate_fhir_schema(state: PipelineState) -> PipelineState:
    """Step 4: Pydantic 기반 FHIR R4 스키마 강제 검증 (Schema Validator)"""
    try:
        # TODO: FHIR R4 Pydantic 모델 검증 (예: PatientModel.model_validate(state["fhir_json"]))
        is_valid = True  # 검증 성공 가정
        if is_valid:
            return {"validation_error": None}
    except Exception as e:
        # 검증 실패 시 에러 메시지 기록 및 카운트 증가
        return {
            "validation_error": str(e),
            "retry_count": state.get("retry_count", 0) + 1
        }

# 3. 조건부 분기 (Edge Routing) 함수
def validation_router(state: PipelineState) -> str:
    """Pydantic 검증 결과 및 재시도 횟수에 따른 라우팅"""
    if state.get("validation_error") is None:
        return "success"
    elif state.get("retry_count", 0) >= 3:
        # 최대 재시도 횟수 초과 시 파이프라인 종료 (또는 에러 핸들러 노드로 이동)
        return "max_retries_exceeded"
    else:
        return "retry"

# 4. 그래프 구성 (Workflow Compilation)
workflow = StateGraph(PipelineState)

# 노드 등록 (Snake Case 식별자 사용)
workflow.add_node("mask_pii", mask_pii_data)
workflow.add_node("retrieve_ontology", retrieve_medical_ontology)
workflow.add_node("map_to_fhir", map_to_fhir_schema)
workflow.add_node("validate_schema", validate_fhir_schema)

# 엣지 연결 (순차 실행 구간)
workflow.set_entry_point("mask_pii")
workflow.add_edge("mask_pii", "retrieve_ontology")
workflow.add_edge("retrieve_ontology", "map_to_fhir")
workflow.add_edge("map_to_fhir", "validate_schema")

# 조건부 엣지 연결 (Retry Loop 구간)
workflow.add_conditional_edges(
    "validate_schema",
    validation_router,
    {
        "success": END,               # 검증 성공 -> 최종 출력
        "retry": "map_to_fhir",        # 검증 실패 -> Step 3(map_to_fhir)로 돌아가 재추론
        "max_retries_exceeded": END   # 최대 재시도 초과 -> 종료
    }
)

# 그래프 컴파일
app = workflow.compile()

