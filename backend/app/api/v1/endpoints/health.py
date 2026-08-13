"""
헬스 체크 API
"""

from typing import Any

from fastapi import APIRouter, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.core.logging import get_logger
from app.db.session import AsyncSessionLocal


logger = get_logger(__name__)

router = APIRouter()


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    summary="기본 상태 확인",
)
async def health_check() -> dict[str, Any]:
    """
    앱 상태 확인
    """

    return {
        "success": True,
        "status": "ok",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
    }


@router.get(
    "/db",
    status_code=status.HTTP_200_OK,
    summary="DB 연결 상태 확인",
)
async def database_health_check() -> dict[str, Any]:
    """
    DB 연결 확인
    """

    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT 1"))
            value = result.scalar_one()

        return {
            "success": True,
            "status": "ok",
            "database": "connected",
            "result": value,
        }

    except SQLAlchemyError as exc:
        logger.exception("DB 헬스 체크 실패.")

        return {
            "success": False,
            "status": "error",
            "database": "disconnected",
            "message": "DB 연결 확인에 실패했습니다.",
            "error": exc.__class__.__name__,
        }


@router.get(
    "/vector",
    status_code=status.HTTP_200_OK,
    summary="pgvector 확장 상태 확인",
)
async def vector_health_check() -> dict[str, Any]:
    """
    pgvector 확장 확인
    """

    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                text(
                    """
                    SELECT EXISTS (
                        SELECT 1
                        FROM pg_extension
                        WHERE extname = 'vector'
                    )
                    """
                )
            )
            exists = bool(result.scalar_one())

        return {
            "success": exists,
            "status": "ok" if exists else "error",
            "extension": "vector",
            "installed": exists,
        }

    except SQLAlchemyError as exc:
        logger.exception("pgvector 헬스 체크 실패.")

        return {
            "success": False,
            "status": "error",
            "extension": "vector",
            "installed": False,
            "message": "pgvector 확장 확인에 실패했습니다.",
            "error": exc.__class__.__name__,
        }

