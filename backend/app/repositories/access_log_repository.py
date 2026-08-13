"""
출입 로그 Repository
시공간 조회는 SQL + 파이썬 거리 계산용 데이터 조회까지만 담당
"""

from collections.abc import Sequence
from datetime import datetime, timedelta

from sqlalchemy import and_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import DatabaseTransactionError
from app.core.logging import get_logger
from app.db.models.access_log import AccessLog
from app.db.models.location import Location
from app.db.models.patient import Patient
from app.schemas.access_log import AccessLogCreate


logger = get_logger(__name__)


class AccessLogRepository:
    """
    출입 로그 DB 접근 계층
    """

    def __init__(self, db: AsyncSession) -> None:
        """
        Repository 초기화
        """

        self.db = db

    async def get_by_id(self, access_log_id: int) -> AccessLog | None:
        """
        ID로 출입 로그 조회
        """

        stmt = (
            select(AccessLog)
            .options(
                selectinload(AccessLog.patient),
                selectinload(AccessLog.location),
            )
            .where(AccessLog.id == access_log_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_patient(
        self,
        *,
        patient_id: int,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int = 200,
    ) -> Sequence[AccessLog]:
        """
        환자별 출입 로그 조회
        """

        conditions = [AccessLog.patient_id == patient_id]

        if start_time is not None:
            conditions.append(AccessLog.occurred_at >= start_time)

        if end_time is not None:
            conditions.append(AccessLog.occurred_at <= end_time)

        stmt = (
            select(AccessLog)
            .options(selectinload(AccessLog.location))
            .where(and_(*conditions))
            .order_by(AccessLog.occurred_at.asc())
            .limit(limit)
        )

        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def list_by_location_and_time_window(
        self,
        *,
        location_id: int,
        start_time: datetime,
        end_time: datetime,
        exclude_patient_id: int | None = None,
        limit: int = 500,
    ) -> Sequence[AccessLog]:
        """
        위치+시간 범위로 로그 조회
        """

        conditions = [
            AccessLog.location_id == location_id,
            AccessLog.occurred_at >= start_time,
            AccessLog.occurred_at <= end_time,
        ]

        if exclude_patient_id is not None:
            conditions.append(AccessLog.patient_id != exclude_patient_id)

        stmt = (
            select(AccessLog)
            .options(
                selectinload(AccessLog.patient),
                selectinload(AccessLog.location),
            )
            .where(and_(*conditions))
            .order_by(AccessLog.occurred_at.asc())
            .limit(limit)
        )

        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def find_logs_near_patient_route(
        self,
        *,
        index_patient_id: int,
        start_time: datetime,
        end_time: datetime,
        time_window_minutes: int = 30,
    ) -> Sequence[AccessLog]:
        """
        기준 환자 동선 주변 로그 조회
        """

        index_logs = await self.list_by_patient(
            patient_id=index_patient_id,
            start_time=start_time,
            end_time=end_time,
        )

        if not index_logs:
            return []

        candidate_logs: list[AccessLog] = []

        for index_log in index_logs:
            window_start = index_log.occurred_at - timedelta(minutes=time_window_minutes)
            window_end = index_log.occurred_at + timedelta(minutes=time_window_minutes)

            logs = await self.list_by_location_and_time_window(
                location_id=index_log.location_id,
                start_time=window_start,
                end_time=window_end,
                exclude_patient_id=index_patient_id,
            )

            candidate_logs.extend(logs)

        return candidate_logs

    async def create(self, access_log_in: AccessLogCreate) -> AccessLog:
        """
        출입 로그 생성
        """

        access_log = AccessLog(**access_log_in.model_dump())

        try:
            self.db.add(access_log)
            await self.db.flush()
            await self.db.refresh(access_log)
            return access_log

        except SQLAlchemyError as exc:
            logger.exception("출입 로그 생성 실패.")
            raise DatabaseTransactionError(
                "출입 로그 생성 중 DB 오류가 발생했습니다."
            ) from exc

    async def get_patient_location_logs_for_contact_trace(
        self,
        *,
        index_patient_id: int,
        start_time: datetime,
        end_time: datetime,
        time_window_minutes: int,
    ) -> tuple[Sequence[AccessLog], Sequence[AccessLog]]:
        """
        접촉 추적용 기준 로그와 후보 로그 조회
        """

        index_logs = await self.list_by_patient(
            patient_id=index_patient_id,
            start_time=start_time,
            end_time=end_time,
        )

        candidate_logs = await self.find_logs_near_patient_route(
            index_patient_id=index_patient_id,
            start_time=start_time,
            end_time=end_time,
            time_window_minutes=time_window_minutes,
        )

        return index_logs, candidate_logs
