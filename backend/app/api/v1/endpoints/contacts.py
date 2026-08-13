"""
접촉자 탐색 API
"""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.access_log import ContactCandidate
from app.services.contact_tracing_service import ContactTracingService


router = APIRouter()


@router.get(
    "/candidates",
    response_model=list[ContactCandidate],
    status_code=status.HTTP_200_OK,
    summary="접촉 후보자 탐색",
)
async def find_contact_candidates(
    index_patient_id: int = Query(gt=0, description="기준 환자 ID"),
    start_time: datetime = Query(description="조회 시작 시각"),
    end_time: datetime = Query(description="조회 종료 시각"),
    time_window_minutes: int = Query(default=30, ge=1, le=1440),
    distance_threshold: float | None = Query(default=None, gt=0),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    접촉 후보자 탐색
    """

    service = ContactTracingService(db)

    return await service.find_contact_candidates(
        index_patient_id=index_patient_id,
        start_time=start_time,
        end_time=end_time,
        time_window_minutes=time_window_minutes,
        distance_threshold=distance_threshold,
    )
