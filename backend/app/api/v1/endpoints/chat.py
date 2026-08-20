"""
채팅 API
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.rag_service import RagService


router = APIRouter()


@router.post(
    "",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="RAG 기반 감염관리 답변 생성",
)
async def chat(
    chat_in: ChatRequest,
    db: AsyncSession = Depends(get_db),
) -> ChatResponse:
    """
    사용자 질문에 대해 지침서 기반 답변 생성
    """

    service = RagService(db)
    return await service.answer_question(chat_in)
