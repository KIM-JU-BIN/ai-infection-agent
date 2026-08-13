"""
감염관리 지침서 ORM 모델
"""

from datetime import datetime
from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class SopDocument(Base):
    """
    RAG 검색용 지침서 청크
    내부 SOP, KDCA, CDC 등 출처를 함께 저장
    """

    __tablename__ = "sop_documents"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
        comment="지침서 PK",
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

    source_type: Mapped[str] = mapped_column(
        String(50),
        index=True,
        nullable=False,
        comment="문서 출처 유형",
    )

    authority: Mapped[str | None] = mapped_column(
        String(100),
        index=True,
        nullable=True,
        comment="발행 기관",
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
        comment="원본 경로 또는 URL",
    )

    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="추가 메타데이터",
    )

    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(1536),
        nullable=True,
        comment="임베딩 벡터",
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
            "ix_sop_documents_source_disease",
            "source_type",
            "disease_type",
        ),
        Index(
            "ix_sop_documents_authority_disease",
            "authority",
            "disease_type",
        ),
        Index(
            "ix_sop_documents_metadata_json_gin",
            "metadata_json",
            postgresql_using="gin",
        ),
        Index(
            "ix_sop_documents_embedding_hnsw",
            "embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )

