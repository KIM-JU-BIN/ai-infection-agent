def create_rag_query_node(state):
    patient_id = state.get("patient_id", "")
    patient_info = state.get("patient_info", {})
    contacts = state.get("contacts", [])


    query = f"""
코로나19 감염 위험 역학조사를 수행한다.

조사 대상 환자:
{patient_id}

환자 정보:
{patient_info}

동선이 겹치는 환자:
{contacts}

위 정보를 바탕으로 다음 내용을 확인한다.

1. 코로나19 확진환자와 동일 공간에 있었던 환자의 감염 위험 평가 기준
2. 의료기관 내 접촉자 및 밀접접촉자 판단 기준
3. 의료기관 내 접촉자 관리 기준
4. 추가로 필요한 검사 및 관리 기준
"""

    return {
        "rag_query": query
    }