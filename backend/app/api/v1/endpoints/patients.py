"""
환자 API
"""

from typing import Any

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.patient import PatientCreate, PatientRead, PatientUpdate
from app.services.patient_service import PatientService


router = APIRouter()


@router.get(
    "",
    response_model=list[PatientRead],
    status_code=status.HTTP_200_OK,
    summary="환자 목록 조회",
)
async def list_patients(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    환자 목록
    """

    service = PatientService(db)
    return await service.list_patients(offset=offset, limit=limit)


@router.post(
    "",
    response_model=PatientRead,
    status_code=status.HTTP_201_CREATED,
    summary="환자 생성",
)
async def create_patient(
    patient_in: PatientCreate,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    환자 생성
    """

    service = PatientService(db)
    patient = await service.create_patient(patient_in)
    await db.commit()
    return patient


@router.get(
    "/{patient_id}",
    response_model=PatientRead,
    status_code=status.HTTP_200_OK,
    summary="환자 단건 조회",
)
async def get_patient(
    patient_id: int,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    환자 단건
    """

    service = PatientService(db)
    return await service.get_patient(patient_id)


@router.patch(
    "/{patient_id}",
    response_model=PatientRead,
    status_code=status.HTTP_200_OK,
    summary="환자 수정",
)
async def update_patient(
    patient_id: int,
    patient_in: PatientUpdate,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    환자 수정
    """

    service = PatientService(db)
    patient = await service.update_patient(patient_id, patient_in)
    await db.commit()
    return patient


@router.delete(
    "/{patient_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="환자 삭제",
)
async def delete_patient(
    patient_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    환자 삭제
    """

    service = PatientService(db)
    await service.delete_patient(patient_id)
    await db.commit()
