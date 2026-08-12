"""
감염관리 SOP 문서 ORM 모델
"""

from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class SopDocument(Base):
    """
    RAG 검색용 SOP 청크
    """

    __tablename__ = "sop_documents"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
        comment="SOP 문서 PK",
    )

    document_code: Mapped[str] = mapped_column(
        String(100),
        index=True,
        nullable=False,
        comment="문서 코드",
    )

    title: Mapped[str] = mapped_column(
        String(300),
        nullable=False,
        comment="문서 제목",
    )

    disease_type: Mapped[str | None] = mapped_column(
        String(100),
        index=True,
        nullable=True,
        comment="감염병 유형",
    )

    section: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        comment="문서 섹션",
    )

    chunk_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="청크 순번",
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="청크 본문",
    )

    source_path: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="원본 파일 경로",
    )

    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(1536),
        nullable=True,
        comment="문서 임베딩 벡터",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="생성 시각",
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="수정 시각",
    )

    __table_args__ = (
        Index(
            "ix_sop_documents_doc_chunk",
            "document_code",
            "chunk_index",
            unique=True,
        ),
        Index(
            "ix_sop_documents_embedding_hnsw",
            "embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )
