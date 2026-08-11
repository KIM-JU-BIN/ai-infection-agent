from langchain_chroma import Chroma
from app.rag.embedding import embeddings


def create_vector_store(documents):
    vector_store = Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        persist_directory="./chroma_db"
        # 프로젝트 폴더 안에  chroma_db의 폴더가 자동으로 생겨서 벡터가 저장된다는 뜻
        # PostgreSQL 대신 폴더가 DB역할을 함
    )

    return vector_store


# 검색 함수 생성
def load_vector_store():
    return Chroma(
        persist_directory="./chroma_db",
        embedding_function=embeddings
    )