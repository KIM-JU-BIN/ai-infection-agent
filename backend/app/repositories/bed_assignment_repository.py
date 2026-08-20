"""
병상 배정 Repository
동일 병실 + 시간 겹침 접촉자를 찾는다
"""

from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.bed_assignment import BedAssignment


class BedAssignmentRepository:
    """
    병상 배정 DB 접근 계층
    """

    def __init__(self, db: AsyncSession) -> None:
        """
        Repository 초기화
        """

        self.db = db

    async def list_by_patient(
        self,
        *,
        patient_id: int,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> Sequence[BedAssignment]:
        """
        특정 환자의 병상 배정 조회
        """

        conditions = [BedAssignment.patient_id == patient_id]

        if start_time is not None and end_time is not None:
            conditions.append(
                self._periods_overlap(
                    admitted_at=BedAssignment.admitted_at,
                    discharged_at=BedAssignment.discharged_at,
                    start_time=start_time,
                    end_time=end_time,
                )
            )

        stmt = (
            select(BedAssignment)
            .options(
                selectinload(BedAssignment.patient),
                selectinload(BedAssignment.location),
            )
            .where(and_(*conditions))
            .order_by(BedAssignment.admitted_at.asc())
        )

        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def find_overlapping_patients(
        self,
        *,
        patient_id: int,
        start_time: datetime,
        end_time: datetime,
    ) -> Sequence[BedAssignment]:
        """
        같은 병실에 같은 시간대 머문 다른 환자 조회
        """

        index_assignments = await self.list_by_patient(
            patient_id=patient_id,
            start_time=start_time,
            end_time=end_time,
        )

        if not index_assignments:
            return []

        candidate_assignments: list[BedAssignment] = []

        for index_assignment in index_assignments:
            overlap_start = max(index_assignment.admitted_at, start_time)

            if index_assignment.discharged_at is None:
                overlap_end = end_time
            else:
                overlap_end = min(index_assignment.discharged_at, end_time)

            stmt = (
                select(BedAssignment)
                .options(
                    selectinload(BedAssignment.patient),
                    selectinload(BedAssignment.location),
                )
                .where(
                    and_(
                        BedAssignment.patient_id != patient_id,
                        BedAssignment.location_id == index_assignment.location_id,
                        self._periods_overlap(
                            admitted_at=BedAssignment.admitted_at,
                            discharged_at=BedAssignment.discharged_at,
                            start_time=overlap_start,
                            end_time=overlap_end,
                        ),
                    )
                )
                .order_by(BedAssignment.admitted_at.asc())
            )

            result = await self.db.execute(stmt)
            candidate_assignments.extend(result.scalars().all())

        return candidate_assignments

    @staticmethod
    def _periods_overlap(
        *,
        admitted_at,
        discharged_at,
        start_time: datetime,
        end_time: datetime,
    ):
        """
        기간 겹침 조건
        discharged_at이 NULL이면 아직 재실 중으로 본다
        """

        return and_(
            admitted_at <= end_time,
            or_(
                discharged_at.is_(None),
                discharged_at >= start_time,
            ),
        )
