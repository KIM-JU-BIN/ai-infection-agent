import json
from app.agent.state import InvestigationState
from app.agent.llm import llm

from app.tools.patient_tool import get_patient_info
from app.tools.emr_tool import get_patient_emr
from app.tools.access_tool import get_patient_access_logs
from app.tools.contact_tool import get_contacts


def load_patient_node(
    state: InvestigationState
):
    """
    환자 정보를 조회
    """
    patient = get_patient_info(
        state["patient_id"]
    )
    state["patient_info"] = patient

    return state


def load_emr_node(
    state: InvestigationState
):
    """
    EMR 조회
    """
    emr = get_patient_emr(
        state["patient_id"]
    )
    state["emr_records"] = emr

    return state


def load_access_node(
    state: InvestigationState
):
    """
    출입기록 조회
    """
    logs = get_patient_access_logs(
        state["patient_id"]
    )
    state["access_logs"] = logs

    return state


def load_contact_node(
    state: InvestigationState
):
    """
    접촉자 조회
    """

    contacts = get_contacts(
        state["patient_id"]
    )

    state["contacts"] = contacts

    return state


def analyze_node(state):
    """
    환자의 감염 상태를 먼저 코드로 판단한 뒤,
    RAG 근거와 접촉 정보를 GPT에 전달하여
    구조화된 감염관리 조사 결과를 생성한다.
    """

    # --------------------------------------------------
    # 1. 환자 기본 정보
    # --------------------------------------------------

    patient_info = state["patient_info"]

    patient_id = state["patient_id"]

    diagnosis = patient_info.get("diagnosis", "")


    # --------------------------------------------------
    # 2. 환자의 조사 역할은 Python이 결정
    # --------------------------------------------------

    if "COVID-19 확진" in diagnosis:
        infection_status = "확진"
        investigation_role = "지표환자"

    elif "COVID-19 의심" in diagnosis:
        infection_status = "의심"
        investigation_role = "일반 조사대상"

    else:
        infection_status = "미확인"
        investigation_role = "접촉자"


    # --------------------------------------------------
    # 3. 접촉 방향 결정
    # --------------------------------------------------

    raw_contacts = state.get("contacts", [])
    
    
    # 관련 환자의 기본 정보를 함께 조회
    related_patients = []

    for contact in raw_contacts:

        related_patient_id = contact.get("patient_id")

        if not related_patient_id:
            continue

        patient_data = get_patient_info(related_patient_id)

        related_patients.append({
            "patient_id": related_patient_id,
            "diagnosis": patient_data.get("diagnosis", "확인 불가"),
            "current_location_id": patient_data.get(
                "current_location_id",
                "확인 불가"
            )
        })
        

    if investigation_role == "지표환자":

        # 확진 환자를 조사하면
        # contacts = 이 환자에게 노출된 사람들

        contacts = raw_contacts
        exposure_sources = []

    else:

        # 확진 환자가 아닌 환자를 조사하면
        # exposure_sources = 이 환자가 노출된 확진/의심 환자

        contacts = []
        exposure_sources = raw_contacts


    # --------------------------------------------------
    # 4. RAG 검색 결과
    # --------------------------------------------------

    rag_context = state.get("rag_context", [])

    rag_text = ""

    for i, item in enumerate(rag_context, start=1):

        rag_text += f"""
[근거 문서 {i}]
출처: {item.get("source")}
페이지: {item.get("page")}
내용:
{item.get("content")}
"""


    # --------------------------------------------------
    # 5. GPT에게 전달할 조사 정보
    # --------------------------------------------------

    prompt = f"""
당신은 병원 감염관리 담당자를 지원하는 AI Agent입니다.

아래 정보를 기반으로 감염관리 역학조사 결과의 초안을 작성하세요.

[조사 대상 환자]
환자 ID: {patient_id}

[환자 정보]
{patient_info}

[감염 상태]
{infection_status}

[조사 역할]
{investigation_role}

[EMR]
{state["emr_records"]}

[출입기록]
{state["access_logs"]}

[접촉자 또는 노출원 정보]
{related_patients}

[공식 감염관리 문서]
{rag_text}


### 중요 규칙

1. 조사 대상 환자의 감염 상태와 조사 역할은
   이미 시스템에서 결정되었습니다.

2. 다음 값을 임의로 변경하지 마세요.

감염 상태:
{infection_status}

조사 역할:
{investigation_role}


3. 조사 역할이 "지표환자"인 경우:

- contacts에 조사 대상 환자에게 노출된 다른 환자를 기록하세요.
- exposure_sources는 빈 배열로 유지하세요.
- 각 접촉자의 노출 위험도를 평가하세요.


4. 조사 역할이 "접촉자" 또는 "일반 조사대상"인 경우:

- contacts는 빈 배열로 유지하세요.
- exposure_sources에 조사 대상 환자가 노출되었을 가능성이 있는 환자를 기록하세요.
- 이때 exposure_risk는 "조사 대상 환자 본인의 노출 위험도"입니다.


5. 감염 상태와 노출 위험도를 혼동하지 마세요.

예를 들어:

P004의 감염 상태 = 미확인

P004가 확진환자 P001과 접촉했다면:

P004의 노출 위험도 = 중간

이라고 표현해야 합니다.

P001의 위험도가 중간이라는 의미가 아닙니다.


6. 공식 감염관리 문서에서 확인되는 내용을
판단 근거로 활용하세요.

7. 공식 문서에서 충분한 근거를 찾을 수 없는 경우
추측하지 말고 추가 조사가 필요하다고 표시하세요.

8. AI의 결과는 감염관리 담당자가 검토하는
"조사 의견서 초안"입니다.

AI가 최종 의료적 판단이나 확진을 결정하지 않습니다.

9. 관련 환자를 표시할 때는 반드시 patient_id를 사용하세요.
환자의 이름은 출력하지 마세요.

10. 조사 대상이 접촉자인 경우 exposure_sources에는
노출원 환자의 patient_id와 감염 상태를 함께 표시하세요.

예:
P001
감염 상태: 확진

11. 노출 위험도는 조사 대상 환자에게 적용되는 값입니다.
노출원 환자의 위험도로 표현하지 마세요.




### 출력 형식

반드시 JSON만 출력하세요.

{{
    "patient_id": "{patient_id}",
    "infection_status": "{infection_status}",
    "investigation_role": "{investigation_role}",

    "contacts": [],

    "exposure_sources": [
        {{   
            "patient_id": "P001",
            "infection_status": "확진",
            "exposure_risk_for_subject": "중간",
            "priority": 1,
            "reason": "P001은 COVID-19 확진자로 확인되었으며 P004와 ER-01에서 45분간 동선이 중복됨."
        }}
    ],

    "sop_evidence": [
        {{
            "source": "문서명",
            "page": "페이지",
            "reason": "판단에 사용한 이유"
        }}
    ],

    "investigation_opinion": "감염관리 담당자가 검토할 조사 의견서 초안",

    "additional_investigation": [
        "추가 조사사항 1",
        "추가 조사사항 2"
    ]
}}

"""


    # --------------------------------------------------
    # 6. GPT 호출
    # --------------------------------------------------

    response = llm.invoke(prompt)

    content = response.content.strip()


    # --------------------------------------------------
    # 7. Markdown JSON 제거
    # --------------------------------------------------

    if content.startswith("```json"):
        content = content[7:]

    elif content.startswith("```"):
        content = content[3:]

    if content.endswith("```"):
        content = content[:-3]

    content = content.strip()


    # --------------------------------------------------
    # 8. JSON 변환
    # --------------------------------------------------

    try:

        result = json.loads(content)

    except json.JSONDecodeError:

        result = {
            "patient_id": patient_id,
            "infection_status": infection_status,
            "investigation_role": investigation_role,
            "contacts": contacts,
            "exposure_sources": exposure_sources,
            "sop_evidence": [],
            "investigation_opinion": response.content,
            "additional_investigation": [
                "AI 응답 형식 확인 필요"
            ]
        }


    # --------------------------------------------------
    # 9. Python에서 결정한 관계를 최종적으로 보정
    # --------------------------------------------------

    if investigation_role == "지표환자":

        result["contacts"] = result.get("contacts", contacts)
        result["exposure_sources"] = []

    else:

        result["contacts"] = []
        result["exposure_sources"] = result.get(
            "exposure_sources",
            exposure_sources
        )


    # 시스템에서 결정한 값은 GPT가 바꾸지 못하도록 다시 설정
    result["patient_id"] = patient_id
    result["infection_status"] = infection_status
    result["investigation_role"] = investigation_role


    # --------------------------------------------------
    # 10. State에 결과 저장
    # --------------------------------------------------

    state["investigation_result"] = result

    return state