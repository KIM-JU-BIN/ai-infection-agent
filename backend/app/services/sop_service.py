"""
지침서 Service
임베딩 동기화와 비즈니스 로직을 담당
"""

from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ResourceNotFoundError
from app.db.models.sop_document import SopDocument
from app.repositories.sop_repository import SopRepository
from app.llm.embedding_client import EmbeddingClient
from app.schemas.sop_document import (
    SopDocumentCreate,
    SopDocumentSearchRequest,
    SopDocumentSearchResult,
    SopDocumentUpdate,
)


class SopService:
    """
    지침서 비즈니스 계층
    """

    def __init__(self, db: AsyncSession) -> None:
        """
        Service 초기화
        """

        self.repository = SopRepository(db)
        self.embedding_client = EmbeddingClient()

    async def get_document(self, sop_id: int) -> SopDocument:
        """
        지침서 단건 조회
        """

        document = await self.repository.get_by_id(sop_id)

        if document is None:
            raise ResourceNotFoundError("SopDocument", sop_id)

        return document

    async def list_documents(
        self,
        *,
        offset: int = 0,
        limit: int = 50,
        source_type: str | None = None,
        authority: str | None = None,
        disease_type: str | None = None,
    ) -> Sequence[SopDocument]:
        """
        지침서 목록 조회
        """

        safe_offset = max(offset, 0)
        safe_limit = min(max(limit, 1), 100)

        return await self.repository.list_documents(
            offset=safe_offset,
            limit=safe_limit,
            source_type=source_type,
            authority=authority,
            disease_type=disease_type,
        )

    async def create_document(self, sop_in: SopDocumentCreate) -> SopDocument:
        """
        지침서 생성
        생성 시 임베딩 자동 저장
        """

        embedding = await self.embedding_client.embed_text(sop_in.content)

        return await self.repository.create(
            sop_in=sop_in,
            embedding=embedding,
        )

    async def update_document(
        self,
        sop_id: int,
        sop_in: SopDocumentUpdate,
    ) -> SopDocument:
        """
        지침서 수정
        본문 변경 시 임베딩 자동 갱신
        """

        document = await self.get_document(sop_id)

        embedding: list[float] | None = None

        if sop_in.content is not None:
            embedding = await self.embedding_client.embed_text(sop_in.content)

        return await self.repository.update(
            document=document,
            sop_in=sop_in,
            embedding=embedding,
        )

    async def delete_document(self, sop_id: int) -> None:
        """
        지침서 삭제.
        """

        document = await self.get_document(sop_id)
        await self.repository.delete(document)

    async def search_documents(
        self,
        search_in: SopDocumentSearchRequest,
    ) -> list[SopDocumentSearchResult]:
        """
        지침서 벡터 검색
        출처/기관/감염병 필터 지원
        """

        query_embedding = await self.embedding_client.embed_text(search_in.query)

        rows = await self.repository.search_by_vector(
            query_embedding=query_embedding,
            top_k=search_in.top_k,
            source_type=search_in.source_type.value if search_in.source_type else None,
            authority=search_in.authority,
            disease_type=search_in.disease_type,
        )

        return [
            SopDocumentSearchResult(
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
                distance=distance,
            )
            for document, distance in rows
        ]
