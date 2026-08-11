from app.rag.retriever import retrieve_documents


def rag_search_node(state):
    """
    현재 조사 질문을 기반으로 SOP/KDCA/CDC 문서를 검색한다.
    """

    query = state.get("rag_query", "")

    if not query:
        return {
            "rag_context": []
        }

    documents = retrieve_documents(
        query=query,
        k=3
    )

    rag_context = []

    for doc in documents:
        rag_context.append({
            "content": doc.page_content,
            "source": doc.metadata.get("source"),
            "page": doc.metadata.get("page")
        })

    return {
        "rag_context": rag_context
    }