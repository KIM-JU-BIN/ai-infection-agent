from langgraph.graph import StateGraph, START, END

from app.agent.state import InvestigationState
from app.agent.nodes import (
    load_patient_node,
    load_emr_node,
    load_access_node,
    load_contact_node,
    analyze_node,
)

from app.agent.rag_query_node import create_rag_query_node
from app.agent.rag_node import rag_search_node


# 환자 정보 -> EMR -> 동선 -> 접촉자 -> 공식 지침 검색 -> GPT 분석

# Graph 생성
builder = StateGraph(InvestigationState)

# Node 등록
builder.add_node("patient", load_patient_node)
builder.add_node("emr", load_emr_node)
builder.add_node("access", load_access_node)
builder.add_node("contact", load_contact_node)

# RAG Node
builder.add_node("create_rag_query", create_rag_query_node)
builder.add_node("rag_search", rag_search_node)

builder.add_node("analyze", analyze_node)


# Edge 연결
builder.add_edge(START, "patient")
builder.add_edge("patient", "emr")
builder.add_edge("emr", "access")
builder.add_edge("access", "contact")

# contact -> RAG 질문 생성 -> 문서 검색 -> 분석
# Contact 정보 확인 후 RAG 검색
builder.add_edge("contact", "create_rag_query")
builder.add_edge("create_rag_query", "rag_search")

# RAG 검색 결과를 가지고 최종 분석
builder.add_edge("rag_search", "analyze")

builder.add_edge("analyze", END)

# Compile
graph = builder.compile()


