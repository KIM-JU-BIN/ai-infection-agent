"""
API v1 Router Aggregator.

v1 하위의 모든 endpoint router를 하나로 묶습니다.
main.py에서는 이 api_router만 include하면 됩니다.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import health

api_router = APIRouter()

api_router.include_router(
    health.router,
    prefix="/health",
    tags=["Health"],
)
