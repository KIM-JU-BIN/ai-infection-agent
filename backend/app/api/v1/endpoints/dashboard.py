"""
대시보드 API

접촉자 케이스 목록과 환자 EMR 상세 정보를 제공한다
"""

from typing import Any

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.access_log import AccessLog
from app.db.models.patient import Patient
from app.db.models.post_action import ContactCase, VitalSign
from app.db.session import get_db
from app.schemas.dashboard import (
    DashboardCaseRead,
    PatientBasicInfo,
    PatientEMRDetail,
    RecentAccessLogRead,
    VitalSignRead,
)


router = APIRouter()


@router.get(
    "/cases",
    response_model=list[DashboardCaseRead],
    status_code=status.HTTP_200_OK,
    summary="대시보드 접촉자 케이스 목록",
)
async def list_dashboard_cases(
    limit: int = Query(default=50, ge=1, le=200),
    risk_level: str | None = Query(default=None),
    case_status: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> list[DashboardCaseRead]:
    """
    최근 접촉자 케이스 목록 조회
    """

    stmt = (
        select(ContactCase)
        .options(selectinload(ContactCase.patient))
        .order_by(ContactCase.created_at.desc())
        .limit(limit)
    )

    if risk_level is not None:
        stmt = stmt.where(ContactCase.risk_level == risk_level)

    if case_status is not None:
        stmt = stmt.where(ContactCase.case_status == case_status)

    result = await db.execute(stmt)
    cases = result.scalars().all()

    return [
        DashboardCaseRead(
            case_id=case.id,
            index_patient_id=case.index_patient_id,
            patient_id=case.patient_id,
            patient_identifier=case.patient.patient_identifier
            if case.patient is not None
            else None,
            patient_name=case.patient.name if case.patient is not None else None,
            disease_type=case.disease_type,
            contact_type=case.contact_type,
            risk_level=case.risk_level,
            test_status=case.test_status,
            sms_sent_status=case.sms_sent_status,
            monitoring_status=case.monitoring_status,
            case_status=case.case_status,
            reason=case.reason,
            action_plan=case.action_plan,
            first_exposed_at=case.first_exposed_at,
            last_exposed_at=case.last_exposed_at,
            created_at=case.created_at,
            updated_at=case.updated_at,
        )
        for case in cases
    ]


@router.get(
    "/patients/{patient_id}/emr",
    response_model=PatientEMRDetail,
    status_code=status.HTTP_200_OK,
    summary="환자 EMR 상세 정보",
)
async def get_patient_emr_detail(
    patient_id: int,
    vital_limit: int = Query(default=20, ge=1, le=100),
    access_log_limit: int = Query(default=30, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> PatientEMRDetail:
    """
    환자 기본 정보, 체온 기록, 최근 동선을 한 번에 조회
    """

    patient = await _get_patient_or_404(
        db=db,
        patient_id=patient_id,
    )

    vital_signs = await _get_recent_vital_signs(
        db=db,
        patient_id=patient_id,
        limit=vital_limit,
    )

    access_logs = await _get_recent_access_logs(
        db=db,
        patient_id=patient_id,
        limit=access_log_limit,
    )

    latest_vital = vital_signs[0] if vital_signs else None

    return PatientEMRDetail(
        patient=PatientBasicInfo(
            id=patient.id,
            patient_identifier=patient.patient_identifier,
            name=patient.name,
            age=getattr(patient, "age", None),
            sex=patient.sex,
            current_diagnosis=getattr(patient, "current_diagnosis", None),
            phone_number=patient.phone_number,
            address=patient.address,
        ),
        latest_temperature=latest_vital.temperature if latest_vital else None,
        latest_temperature_recorded_at=latest_vital.recorded_at
        if latest_vital
        else None,
        has_fever=bool(latest_vital and latest_vital.temperature >= 37.5),
        vital_signs=[
            VitalSignRead(
                id=vital.id,
                recorded_at=vital.recorded_at,
                temperature=vital.temperature,
                source_system=vital.source_system,
                note=vital.note,
            )
            for vital in vital_signs
        ],
        recent_access_logs=[
            RecentAccessLogRead(
                id=log.id,
                location_id=log.location_id,
                location_name=log.location.name if log.location else None,
                location_type=log.location.location_type if log.location else None,
                floor=log.location.floor if log.location else None,
                occurred_at=log.occurred_at,
                direction=getattr(log, "direction", None),
                event_type=log.event_type,
            )
            for log in access_logs
        ],
    )


async def _get_patient_or_404(
    *,
    db: AsyncSession,
    patient_id: int,
) -> Patient:
    """
    환자 조회
    """

    stmt = select(Patient).where(Patient.id == patient_id)
    result = await db.execute(stmt)
    patient = result.scalar_one_or_none()

    if patient is None:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="환자를 찾을 수 없습니다.",
        )

    return patient


async def _get_recent_vital_signs(
    *,
    db: AsyncSession,
    patient_id: int,
    limit: int,
) -> list[VitalSign]:
    """
    최근 체온 기록 조회
    """

    stmt = (
        select(VitalSign)
        .where(VitalSign.patient_id == patient_id)
        .order_by(VitalSign.recorded_at.desc())
        .limit(limit)
    )

    result = await db.execute(stmt)
    return list(result.scalars().all())


async def _get_recent_access_logs(
    *,
    db: AsyncSession,
    patient_id: int,
    limit: int,
) -> list[AccessLog]:
    """
    최근 출입 로그 조회
    """

    stmt = (
        select(AccessLog)
        .options(selectinload(AccessLog.location))
        .where(AccessLog.patient_id == patient_id)
        .order_by(AccessLog.occurred_at.desc())
        .limit(limit)
    )

    result = await db.execute(stmt)
    return list(result.scalars().all())
