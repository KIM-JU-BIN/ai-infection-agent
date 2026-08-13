"""
지침서 Repository
DB 접근만 담당
"""

from collections.abc import Sequence
from typing import Any

from sqlalchemy import Select, cast, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ColumnElement

from app.core.exceptions import DatabaseTransactionError
from app.core.logging import get_logger
from app.db.models.sop_document import SopDocument
from app.schemas.sop_document import SopDocumentCreate, SopDocumentUpdate


logger = get_logger(__name__)


class SopRepository:
    """
    지침서 DB 접근 계층
    """

    def __init__(self, db: AsyncSession) -> None:
        """
        Repository 초기화
        """

        self.db = db

    async def get_by_id(self, sop_id: int) -> SopDocument | None:
        """
        ID로 지침서 조회
        """

        stmt = select(SopDocument).where(SopDocument.id == sop_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

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

        stmt = select(SopDocument)

        stmt = self._apply_filters(
            stmt=stmt,
            source_type=source_type,
            authority=authority,
            disease_type=disease_type,
        )

        stmt = (
            stmt.order_by(SopDocument.id.desc())
            .offset(offset)
            .limit(limit)
        )

        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def create(
        self,
        sop_in: SopDocumentCreate,
        embedding: list[float],
    ) -> SopDocument:
        """
        지침서 생성
        """

        data = sop_in.model_dump()
        data["source_type"] = str(sop_in.source_type.value)
        data["embedding"] = embedding

        document = SopDocument(**data)

        try:
            self.db.add(document)
            await self.db.flush()
            await self.db.refresh(document)
            return document

        except SQLAlchemyError as exc:
            logger.exception("지침서 생성 실패.")
            raise DatabaseTransactionError(
                "지침서 생성 중 DB 오류가 발생했습니다."
            ) from exc

    async def update(
        self,
        document: SopDocument,
        sop_in: SopDocumentUpdate,
        embedding: list[float] | None = None,
    ) -> SopDocument:
        """
        지침서 수정
        """

        update_data = sop_in.model_dump(exclude_unset=True)

        if "source_type" in update_data and update_data["source_type"] is not None:
            update_data["source_type"] = update_data["source_type"].value

        for field, value in update_data.items():
            setattr(document, field, value)

        if embedding is not None:
            document.embedding = embedding

        try:
            await self.db.flush()
            await self.db.refresh(document)
            return document

        except SQLAlchemyError as exc:
            logger.exception("지침서 수정 실패.")
            raise DatabaseTransactionError(
                "지침서 수정 중 DB 오류가 발생했습니다."
            ) from exc

    async def delete(self, document: SopDocument) -> None:
        """
        지침서 삭제
        """

        try:
            await self.db.delete(document)
            await self.db.flush()

        except SQLAlchemyError as exc:
            logger.exception("지침서 삭제 실패.")
            raise DatabaseTransactionError(
                "지침서 삭제 중 DB 오류가 발생했습니다."
            ) from exc

    async def search_by_vector(
        self,
        *,
        query_embedding: list[float],
        top_k: int = 5,
        source_type: str | None = None,
        authority: str | None = None,
        disease_type: str | None = None,
    ) -> list[tuple[SopDocument, float]]:
        """
        pgvector 유사도 검색
        """

        distance_expr = SopDocument.embedding.cosine_distance(query_embedding).label(
            "distance"
        )

        stmt = select(SopDocument, distance_expr).where(
            SopDocument.embedding.is_not(None)
        )

        stmt = self._apply_filters(
            stmt=stmt,
            source_type=source_type,
            authority=authority,
            disease_type=disease_type,
        )

        stmt = stmt.order_by(distance_expr).limit(top_k)

        result = await self.db.execute(stmt)

        return [
            (row[0], float(row[1]))
            for row in result.all()
        ]

    def _apply_filters(
        self,
        *,
        stmt: Select[tuple[Any, ...]],
        source_type: str | None = None,
        authority: str | None = None,
        disease_type: str | None = None,
    ) -> Select[tuple[Any, ...]]:
        """
        메타데이터 필터 적용
        """

        if source_type is not None:
            stmt = stmt.where(SopDocument.source_type == source_type)

        if authority is not None:
            stmt = stmt.where(SopDocument.authority == authority)

        if disease_type is not None:
            stmt = stmt.where(SopDocument.disease_type == disease_type)

        return stmt
