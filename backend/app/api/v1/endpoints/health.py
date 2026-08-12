"""
Health Check API Endpoint.
"""

from fastapi import APIRouter, status

from app.core.config import settings

router = APIRouter()


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    summary="Health check",
)
async def health_check() -> dict[str, str]:
    """
    API 서버의 상태를 확인합니다.

    Returns:
        dict[str, str]: 서버 상태 정보.
    """

    return {
        "status": "ok",
        "service": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
    }
