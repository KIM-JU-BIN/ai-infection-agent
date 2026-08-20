"""
접촉자 위험도 평가 API
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.assessment import AssessmentRequest, AssessmentResponse
from app.services.assessment_service import AssessmentService


router = APIRouter()


@router.post(
    "/patients/{patient_id}/assess",
    response_model=AssessmentResponse,
    status_code=status.HTTP_200_OK,
    summary="접촉자 위험도 자동 평가",
)
async def assess_patient_contacts(
    patient_id: int,
    request: AssessmentRequest,
    db: AsyncSession = Depends(get_db),
) -> AssessmentResponse:
    """
    기준 환자의 접촉자 위험도 평가
    """

    service = AssessmentService(db)

    response = await service.assess_contacts(
        patient_id=patient_id,
        request=request,
    )

    await db.commit()

    return response

