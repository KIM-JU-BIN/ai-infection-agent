"""
API v1 라우터 통합
"""

from fastapi import APIRouter

from app.api.v1.endpoints import assessment, chat, contacts, health, patients, sop


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

api_router.include_router(
    sop.router,
    prefix="/sop-documents",
    tags=["SOP Documents"],
)

api_router.include_router(
    chat.router,
    prefix="/chat",
    tags=["Chat"],
)

api_router.include_router(
    assessment.router,
    tags=["Assessment"],
)

