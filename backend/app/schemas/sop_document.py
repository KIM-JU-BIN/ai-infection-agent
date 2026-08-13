"""
지침서 스키마
"""

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SopSourceType(StrEnum):
    """
    지침서 출처 유형
    """

    INTERNAL_SOP = "INTERNAL_SOP"
    KDCA = "KDCA"
    CDC = "CDC"
    WHO = "WHO"
    OTHER = "OTHER"


class SopDocumentBase(BaseModel):
    """
    지침서 공통 필드
    """

    document_code: str = Field(
        min_length=1,
        max_length=100,
        description="문서 코드",
    )

    title: str = Field(
        min_length=1,
        max_length=300,
        description="문서 제목",
    )

    source_type: SopSourceType = Field(
        description="문서 출처 유형",
    )

    authority: str | None = Field(
        default=None,
        max_length=100,
        description="발행 기관",
    )

    disease_type: str | None = Field(
        default=None,
        max_length=100,
        description="감염병 유형",
    )

    section: str | None = Field(
        default=None,
        max_length=200,
        description="문서 섹션",
    )

    chunk_index: int = Field(
        ge=0,
        description="청크 순번",
    )

    content: str = Field(
        min_length=1,
        description="청크 본문",
    )

    source_path: str | None = Field(
        default=None,
        max_length=500,
        description="원본 경로 또는 URL",
    )

    metadata_json: dict[str, Any] | None = Field(
        default=None,
        description="추가 메타데이터",
    )


class SopDocumentCreate(SopDocumentBase):
    """
    지침서 생성 요청
    """

    pass


class SopDocumentUpdate(BaseModel):
    """
    지침서 수정 요청
    """

    document_code: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="문서 코드",
    )

    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=300,
        description="문서 제목",
    )

    source_type: SopSourceType | None = Field(
        default=None,
        description="문서 출처 유형",
    )

    authority: str | None = Field(
        default=None,
        max_length=100,
        description="발행 기관",
    )

    disease_type: str | None = Field(
        default=None,
        max_length=100,
        description="감염병 유형",
    )

    section: str | None = Field(
        default=None,
        max_length=200,
        description="문서 섹션",
    )

    chunk_index: int | None = Field(
        default=None,
        ge=0,
        description="청크 순번",
    )

    content: str | None = Field(
        default=None,
        min_length=1,
        description="청크 본문",
    )

    source_path: str | None = Field(
        default=None,
        max_length=500,
        description="원본 경로 또는 URL",
    )

    metadata_json: dict[str, Any] | None = Field(
        default=None,
        description="추가 메타데이터",
    )


class SopDocumentRead(SopDocumentBase):
    """
    지침서 응답
    """

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="지침서 PK")
    created_at: datetime = Field(description="생성 시각")
    updated_at: datetime = Field(description="수정 시각")
    has_embedding: bool = Field(description="임베딩 존재 여부")


class SopDocumentSearchRequest(BaseModel):
    """
    지침서 검색 요청
    """

    query: str = Field(
        min_length=1,
        description="검색 질문",
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
        le=20,
        description="검색 개수",
    )


class SopDocumentSearchResult(BaseModel):
    """
    지침서 검색 결과
    """

    id: int = Field(description="지침서 PK")
    document_code: str = Field(description="문서 코드")
    title: str = Field(description="문서 제목")
    source_type: str = Field(description="문서 출처")
    authority: str | None = Field(default=None, description="발행 기관")
    disease_type: str | None = Field(default=None, description="감염병 유형")
    section: str | None = Field(default=None, description="섹션")
    chunk_index: int = Field(description="청크 순번")
    content: str = Field(description="본문")
    source_path: str | None = Field(default=None, description="원본 경로")
    distance: float = Field(description="코사인 거리")
