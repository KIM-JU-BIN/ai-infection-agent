"""
RAG Service
검색 + LLM 답변 생성을 담당한다
"""

from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AppError
from app.core.logging import get_logger
from app.repositories.sop_repository import SopRepository
from app.llm.embedding_client import EmbeddingClient
from app.schemas.chat import ChatRequest, ChatResponse, ChatSource


logger = get_logger(__name__)


class RagService:
    """
    지침서 기반 RAG 비즈니스 계층
    """

    def __init__(self, db: AsyncSession) -> None:
        """
        Service 초기화.
        """

        if not settings.OPENAI_API_KEY:
            raise AppError(
                "OPENAI_API_KEY가 설정되지 않았습니다.",
                error_code="OPENAI_CONFIG_ERROR",
                status_code=500,
            )

        self.repository = SopRepository(db)
        self.embedding_client = EmbeddingClient()
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    async def answer_question(self, chat_in: ChatRequest) -> ChatResponse:
        """
        질문에 대한 RAG 답변 생성
        """

        query_embedding = await self.embedding_client.embed_text(chat_in.query)

        search_results = await self.repository.search_by_vector(
            query_embedding=query_embedding,
            top_k=chat_in.top_k,
            source_type=chat_in.source_type.value if chat_in.source_type else None,
            authority=chat_in.authority,
            disease_type=chat_in.disease_type,
        )

        sources = [
            ChatSource(
                document_id=document.id,
                document_code=document.document_code,
                title=document.title,
                source_type=document.source_type,
                authority=document.authority,
                disease_type=document.disease_type,
                section=document.section,
                chunk_index=document.chunk_index,
                source_path=document.source_path,
                distance=distance,
            )
            for document, distance in search_results
        ]

        if not search_results:
            return ChatResponse(
                answer=(
                    "제공된 지침서에서 질문에 답할 수 있는 근거를 찾지 못했습니다. "
                    "관련 SOP, KDCA, CDC 문서를 추가로 등록한 뒤 다시 질문해 주세요."
                ),
                sources=[],
                used_context_count=0,
            )

        context = self._build_context(search_results)

        answer = await self._generate_answer(
            query=chat_in.query,
            context=context,
        )

        return ChatResponse(
            answer=answer,
            sources=sources,
            used_context_count=len(sources),
        )

    async def _generate_answer(
        self,
        *,
        query: str,
        context: str,
    ) -> str:
        """
        LLM 답변 생성
        """

        try:
            response = await self.client.chat.completions.create(
                model=settings.CHAT_MODEL,
                temperature=0.1,
                messages=[
                    {
                        "role": "system",
                        "content": self._build_system_prompt(),
                    },
                    {
                        "role": "user",
                        "content": self._build_user_prompt(
                            query=query,
                            context=context,
                        ),
                    },
                ],
            )

            answer = response.choices[0].message.content

            if not answer:
                raise AppError(
                    "LLM 응답이 비어 있습니다.",
                    error_code="EMPTY_LLM_RESPONSE",
                    status_code=502,
                )

            return answer.strip()

        except AppError:
            raise

        except Exception as exc:
            logger.exception("LLM 답변 생성 실패.")
            raise AppError(
                "LLM 답변 생성에 실패했습니다.",
                error_code="LLM_GENERATION_ERROR",
                status_code=502,
            ) from exc

    @staticmethod
    def _build_system_prompt() -> str:
        """
        시스템 프롬프트
        """

        return """
너는 전문적인 감염관리 AI 에이전트다.

반드시 아래 규칙을 지켜라.

1. 답변은 제공된 지침서 Context에 근거해서만 작성한다.
2. Context에 없는 내용은 절대 추측하지 않는다.
3. 근거가 부족하면 "제공된 지침서만으로는 판단할 수 없습니다"라고 말한다.
4. 의학적 최종 판단이나 처방처럼 단정하지 않는다.
5. 감염관리 담당자가 검토할 수 있도록 실무적인 문장으로 답한다.
6. 가능하면 어떤 출처의 지침에 근거했는지 답변 안에 간단히 언급한다.
7. 환자 개인정보가 포함된 질문이더라도 개인정보를 반복 노출하지 않는다.
8. 답변은 한국어로 작성한다.
""".strip()

    @staticmethod
    def _build_user_prompt(
        *,
        query: str,
        context: str,
    ) -> str:
        """
        사용자 프롬프트
        """

        return f"""
[Context]
{context}

[사용자 질문]
{query}

[답변 지침]
- Context에 있는 내용만 근거로 답변해.
- 근거가 부족하면 부족하다고 말해.
- 핵심 판단, 근거, 추가 확인사항 순서로 간결하게 답변해.
""".strip()

    @staticmethod
    def _build_context(search_results: list[tuple[object, float]]) -> str:
        """
        검색 결과를 프롬프트 Context로 변환
        """

        context_blocks: list[str] = []

        for index, (document, distance) in enumerate(search_results, start=1):
            context_blocks.append(
                f"""
[문서 {index}]
문서ID: {document.id}
문서코드: {document.document_code}
제목: {document.title}
출처: {document.source_type}
기관: {document.authority or "N/A"}
감염병: {document.disease_type or "N/A"}
섹션: {document.section or "N/A"}
청크: {document.chunk_index}
검색거리: {distance}
본문:
{document.content}
""".strip()
            )

        return "\n\n---\n\n".join(context_blocks)
