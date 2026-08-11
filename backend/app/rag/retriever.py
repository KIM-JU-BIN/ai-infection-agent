from app.rag.vector_store import load_vector_store


def retrieve_documents(query: str, k: int = 3):
    """
    질문과 가장 관련 있는 문서를 검색
    """

    db = load_vector_store()

    docs = db.similarity_search(
        query=query,
        k=k
    )

    return docs