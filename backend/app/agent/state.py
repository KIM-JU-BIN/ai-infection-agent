from typing import TypedDict


class InvestigationState(TypedDict):

    patient_id: str
    
    patient_info: dict
    
    emr_records: list
    
    access_logs: list
    
    contacts: list
    
    # RAG
    rag_query: str
    rag_context: list
    
    investigation_result: dict
    