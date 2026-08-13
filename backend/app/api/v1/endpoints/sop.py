"""
지침서 API
"""

from typing import Any

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.sop_document import (
    SopDocumentCreate,
    SopDocumentRead,
    SopDocumentSearchRequest,
    SopDocumentSearchResult,
    SopDocumentUpdate,
    SopSourceType,
)
from app.services.sop_service import SopService


router = APIRouter()


def to_sop_read(document: Any) -> SopDocumentRead:
    """
    ORM을 응답 스키마로 변환
    """

    return SopDocumentRead(
        id=document.id,
        document_code=document.document_code,
        title=document.title,
        source_type=document.source_type,
        authority=document.authority,
        disease_type=document.disease_type,
        section=document.section,
        chunk_index=document.chunk_index,
        content=document.content,
        source_path=document.source_path,
        metadata_json=document.metadata_json,
        created_at=document.created_at,
        updated_at=document.updated_at,
        has_embedding=document.embedding is not None,
    )


@router.get(
    "",
    response_model=list[SopDocumentRead],
    status_code=status.HTTP_200_OK,
    summary="지침서 목록 조회",
)
async def list_sop_documents(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    source_type: SopSourceType | None = Query(default=None),
    authority: str | None = Query(default=None),
    disease_type: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> list[SopDocumentRead]:
    """
    지침서 목록
    """

    service = SopService(db)

    documents = await service.list_documents(
        offset=offset,
        limit=limit,
        source_type=source_type.value if source_type else None,
        authority=authority,
        disease_type=disease_type,
    )

    return [to_sop_read(document) for document in documents]


@router.post(
    "",
    response_model=SopDocumentRead,
    status_code=status.HTTP_201_CREATED,
    summary="지침서 생성",
)
async def create_sop_document(
    sop_in: SopDocumentCreate,
    db: AsyncSession = Depends(get_db),
) -> SopDocumentRead:
    """
    지침서 생성
    임베딩 자동 생성
    """

    service = SopService(db)
    document = await service.create_document(sop_in)
    await db.commit()

    return to_sop_read(document)


@router.get(
    "/{sop_id}",
    response_model=SopDocumentRead,
    status_code=status.HTTP_200_OK,
    summary="지침서 단건 조회",
)
async def get_sop_document(
    sop_id: int,
    db: AsyncSession = Depends(get_db),
) -> SopDocumentRead:
    """
    지침서 단건
    """

    service = SopService(db)
    document = await service.get_document(sop_id)

    return to_sop_read(document)


@router.patch(
    "/{sop_id}",
    response_model=SopDocumentRead,
    status_code=status.HTTP_200_OK,
    summary="지침서 수정",
)
async def update_sop_document(
    sop_id: int,
    sop_in: SopDocumentUpdate,
    db: AsyncSession = Depends(get_db),
) -> SopDocumentRead:
    """
    지침서 수정
    본문 변경 시 임베딩 자동 갱신
    """

    service = SopService(db)
    document = await service.update_document(sop_id, sop_in)
    await db.commit()

    return to_sop_read(document)


@router.delete(
    "/{sop_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="지침서 삭제",
)
async def delete_sop_document(
    sop_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    지침서 삭제
    """

    service = SopService(db)
    await service.delete_document(sop_id)
    await db.commit()


@router.post(
    "/search",
    response_model=list[SopDocumentSearchResult],
    status_code=status.HTTP_200_OK,
    summary="지침서 벡터 검색",
)
async def search_sop_documents(
    search_in: SopDocumentSearchRequest,
    db: AsyncSession = Depends(get_db),
) -> list[SopDocumentSearchResult]:
    """
    지침서 검색
    source_type, authority, disease_type 필터 가능
    """

    service = SopService(db)

    return await service.search_documents(search_in)
