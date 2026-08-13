"""
접촉 추적 Service
PostGIS 없이 x_coord/y_coord로 거리 계산
"""

from datetime import datetime
from math import sqrt

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.access_log import AccessLog
from backend.app.repositories.access_log_repository import AccessLogRepository
from app.schemas.access_log import ContactCandidate


class ContactTracingService:
    """
    접촉자 탐색 비즈니스 계층
    """

    def __init__(self, db: AsyncSession) -> None:
        """
        Service 초기화
        """

        self.repository = AccessLogRepository(db)

    async def find_contact_candidates(
        self,
        *,
        index_patient_id: int,
        start_time: datetime,
        end_time: datetime,
        time_window_minutes: int = 30,
        distance_threshold: float | None = None,
    ) -> list[ContactCandidate]:
        """
        접촉 후보자 탐색
        """

        index_logs, candidate_logs = (
            await self.repository.get_patient_location_logs_for_contact_trace(
                index_patient_id=index_patient_id,
                start_time=start_time,
                end_time=end_time,
                time_window_minutes=time_window_minutes,
            )
        )

        if not index_logs or not candidate_logs:
            return []

        candidates: list[ContactCandidate] = []
        seen_keys: set[tuple[int, int, datetime]] = set()

        for index_log in index_logs:
            for candidate_log in candidate_logs:
                if candidate_log.patient_id == index_patient_id:
                    continue

                if candidate_log.location_id != index_log.location_id:
                    continue

                time_diff_minutes = self._calculate_time_diff_minutes(
                    index_log.occurred_at,
                    candidate_log.occurred_at,
                )

                if time_diff_minutes > time_window_minutes:
                    continue

                distance = self._calculate_distance(index_log, candidate_log)

                if (
                    distance_threshold is not None
                    and distance is not None
                    and distance > distance_threshold
                ):
                    continue

                key = (
                    candidate_log.patient_id,
                    candidate_log.location_id,
                    candidate_log.occurred_at,
                )

                if key in seen_keys:
                    continue

                seen_keys.add(key)

                if candidate_log.patient is None or candidate_log.location is None:
                    continue

                candidates.append(
                    ContactCandidate(
                        patient_id=candidate_log.patient.id,
                        patient_identifier=candidate_log.patient.patient_identifier,
                        patient_name=candidate_log.patient.name,
                        location_id=candidate_log.location.id,
                        location_name=candidate_log.location.name,
                        occurred_at=candidate_log.occurred_at,
                        distance=distance,
                        time_diff_minutes=time_diff_minutes,
                    )
                )

        return sorted(
            candidates,
            key=lambda candidate: (
                candidate.time_diff_minutes,
                candidate.distance if candidate.distance is not None else 999999.0,
            ),
        )

    @staticmethod
    def _calculate_time_diff_minutes(
        base_time: datetime,
        target_time: datetime,
    ) -> float:
        """
        시간 차이 계산
        """

        diff_seconds = abs((base_time - target_time).total_seconds())
        return diff_seconds / 60

    @staticmethod
    def _calculate_distance(
        index_log: AccessLog,
        candidate_log: AccessLog,
    ) -> float | None:
        """
        좌표 거리 계산
        """

        index_location = index_log.location
        candidate_location = candidate_log.location

        if index_location is None or candidate_location is None:
            return None

        if index_location.x_coord is None or index_location.y_coord is None:
            return None

        if candidate_location.x_coord is None or candidate_location.y_coord is None:
            return None

        x_diff = index_location.x_coord - candidate_location.x_coord
        y_diff = index_location.y_coord - candidate_location.y_coord

        return sqrt((x_diff * x_diff) + (y_diff * y_diff))
