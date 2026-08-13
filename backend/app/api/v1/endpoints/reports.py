"""
API v1 라우터 통합
"""

from fastapi import APIRouter

from app.api.v1.endpoints import contacts, health, patients


api_router = APIRouter()

api_router.include_router(
    health.router,
    prefix="/health",
    tags=["Health"],
)

api_router.include_router(
    patients.router,
    prefix="/patients",
    tags=["Patients"],
)

api_router.include_router(
    contacts.router,
    prefix="/contacts",
    tags=["Contacts"],
)
