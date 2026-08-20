"""
채팅/RAG 스키마
"""

from pydantic import BaseModel, Field

from app.schemas.sop_document import SopSourceType


class ChatRequest(BaseModel):
    """
    사용자 질문 요청
    """

    query: str = Field(
        min_length=1,
        description="사용자 질문",
    )

    source_type: SopSourceType | None = Field(
        default=None,
        description="출처 필터",
    )

    authority: str | None = Field(
        default=None,
        max_length=100,
        description="기관 필터",
    )

    disease_type: str | None = Field(
        default=None,
        max_length=100,
        description="감염병 필터",
    )

    top_k: int = Field(
        default=5,
        ge=1,
        le=10,
        description="검색 문서 수",
    )


class ChatSource(BaseModel):
    """
    답변에 사용한 출처
    """

    document_id: int = Field(description="문서 ID")
    document_code: str = Field(description="문서 코드")
    title: str = Field(description="문서 제목")
    source_type: str = Field(description="출처 유형")
    authority: str | None = Field(default=None, description="기관명")
    disease_type: str | None = Field(default=None, description="감염병 유형")
    section: str | None = Field(default=None, description="섹션")
    chunk_index: int = Field(description="청크 순번")
    source_path: str | None = Field(default=None, description="원본 경로")
    distance: float = Field(description="검색 거리")


class ChatResponse(BaseModel):
    """
    RAG 답변 응답
    """

    answer: str = Field(description="AI 답변")
    sources: list[ChatSource] = Field(description="참고 문서 목록")
    used_context_count: int = Field(description="사용한 문서 수")
