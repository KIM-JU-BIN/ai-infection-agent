"""
임베딩 클라이언트
"""

from openai import AsyncOpenAI

from app.core.config import settings
from app.core.exceptions import AppError
from app.core.logging import get_logger


logger = get_logger(__name__)


class EmbeddingClient:
    """
    텍스트 임베딩 생성기
    """

    def __init__(self) -> None:
        """
        클라이언트 초기화
        """

        if not settings.OPENAI_API_KEY:
            raise AppError(
                "OPENAI_API_KEY가 설정되지 않았습니다.",
                error_code="EMBEDDING_CONFIG_ERROR",
                status_code=500,
            )

        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.EMBEDDING_MODEL
        self.dimension = settings.EMBEDDING_DIMENSION

    async def embed_text(self, text: str) -> list[float]:
        """
        단일 텍스트 임베딩
        """

        cleaned_text = text.strip()

        if not cleaned_text:
            raise AppError(
                "임베딩할 텍스트가 비어 있습니다.",
                error_code="EMPTY_EMBEDDING_TEXT",
                status_code=400,
            )

        try:
            response = await self.client.embeddings.create(
                model=self.model,
                input=cleaned_text,
            )

            embedding = response.data[0].embedding

            if len(embedding) != self.dimension:
                raise AppError(
                    "임베딩 차원이 설정값과 다릅니다.",
                    error_code="EMBEDDING_DIMENSION_MISMATCH",
                    status_code=500,
                    details={
                        "expected": self.dimension,
                        "actual": len(embedding),
                    },
                )

            return embedding

        except AppError:
            raise

        except Exception as exc:
            logger.exception("임베딩 생성 실패.")
            raise AppError(
                "임베딩 생성에 실패했습니다.",
                error_code="EMBEDDING_GENERATION_ERROR",
                status_code=502,
            ) from exc
