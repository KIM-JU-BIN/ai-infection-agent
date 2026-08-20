"""
접촉 추적 Service
PostGIS 없이 x_coord/y_coord로 거리 계산
출입 로그 겹침 + 병실 재실 겹침을 함께 봄
"""

from datetime import datetime
from math import sqrt

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.access_log import AccessLog
from app.db.models.bed_assignment import BedAssignment
from app.repositories.access_log_repository import AccessLogRepository
from app.repositories.bed_assignment_repository import BedAssignmentRepository
from app.schemas.access_log import ContactCandidate


class ContactTracingService:
    """
    접촉자 탐색 비즈니스 계층
    """

    def __init__(self, db: AsyncSession) -> None:
        """
        Service 초기화
        """

        self.access_log_repository = AccessLogRepository(db)
        self.bed_assignment_repository = BedAssignmentRepository(db)

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
        최종 접촉 후보자 탐색
        """

        access_log_contacts = await self._find_access_log_contacts(
            index_patient_id=index_patient_id,
            start_time=start_time,
            end_time=end_time,
            time_window_minutes=time_window_minutes,
            distance_threshold=distance_threshold,
        )

        bed_assignment_contacts = await self._find_bed_assignment_contacts(
            index_patient_id=index_patient_id,
            start_time=start_time,
            end_time=end_time,
        )

        return self._merge_contacts(
            access_log_contacts=access_log_contacts,
            bed_assignment_contacts=bed_assignment_contacts,
        )

    async def _find_access_log_contacts(
        self,
        *,
        index_patient_id: int,
        start_time: datetime,
        end_time: datetime,
        time_window_minutes: int,
        distance_threshold: float | None,
    ) -> list[ContactCandidate]:
        """
        출입 로그 기반 접촉자 탐색
        """

        index_logs, candidate_logs = (
            await self.access_log_repository.get_patient_location_logs_for_contact_trace(
                index_patient_id=index_patient_id,
                start_time=start_time,
                end_time=end_time,
                time_window_minutes=time_window_minutes,
            )
        )

        if not index_logs or not candidate_logs:
            return []

        contacts: list[ContactCandidate] = []
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

                distance = self._calculate_access_log_distance(
                    index_log,
                    candidate_log,
                )

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

                contacts.append(
                    ContactCandidate(
                        patient_id=candidate_log.patient.id,
                        patient_identifier=candidate_log.patient.patient_identifier,
                        patient_name=candidate_log.patient.name,
                        location_id=candidate_log.location.id,
                        location_name=candidate_log.location.name,
                        occurred_at=candidate_log.occurred_at,
                        distance=distance,
                        time_diff_minutes=time_diff_minutes,
                        contact_type="ACCESS_LOG_OVERLAP",
                    )
                )

        return contacts

    async def _find_bed_assignment_contacts(
        self,
        *,
        index_patient_id: int,
        start_time: datetime,
        end_time: datetime,
    ) -> list[ContactCandidate]:
        """
        병상 배정 기반 접촉자 탐색
        """

        overlapping_assignments = (
            await self.bed_assignment_repository.find_overlapping_patients(
                patient_id=index_patient_id,
                start_time=start_time,
                end_time=end_time,
            )
        )

        contacts: list[ContactCandidate] = []
        seen_keys: set[tuple[int, int]] = set()

        for assignment in overlapping_assignments:
            if assignment.patient is None or assignment.location is None:
                continue

            key = (assignment.patient_id, assignment.location_id)

            if key in seen_keys:
                continue

            seen_keys.add(key)

            contacts.append(
                ContactCandidate(
                    patient_id=assignment.patient.id,
                    patient_identifier=assignment.patient.patient_identifier,
                    patient_name=assignment.patient.name,
                    location_id=assignment.location.id,
                    location_name=assignment.location.name,
                    occurred_at=assignment.admitted_at,
                    distance=0.0,
                    time_diff_minutes=0.0,
                    contact_type="BED_ASSIGNMENT_OVERLAP",
                )
            )

        return contacts

    @staticmethod
    def _merge_contacts(
        *,
        access_log_contacts: list[ContactCandidate],
        bed_assignment_contacts: list[ContactCandidate],
    ) -> list[ContactCandidate]:
        """
        접촉자 병합
        같은 환자가 여러 방식으로 잡히면 병실 접촉을 우선한다
        """

        merged: dict[int, ContactCandidate] = {}

        for contact in access_log_contacts:
            merged[contact.patient_id] = contact

        for contact in bed_assignment_contacts:
            existing = merged.get(contact.patient_id)

            if existing is None:
                merged[contact.patient_id] = contact
                continue

            merged[contact.patient_id] = ContactCandidate(
                patient_id=contact.patient_id,
                patient_identifier=contact.patient_identifier,
                patient_name=contact.patient_name,
                location_id=contact.location_id,
                location_name=contact.location_name,
                occurred_at=contact.occurred_at,
                distance=contact.distance,
                time_diff_minutes=contact.time_diff_minutes,
                contact_type="BED_ASSIGNMENT_OVERLAP+ACCESS_LOG_OVERLAP",
            )

        return sorted(
            merged.values(),
            key=lambda item: (
                0 if "BED_ASSIGNMENT" in item.contact_type else 1,
                item.time_diff_minutes,
                item.distance if item.distance is not None else 999999.0,
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
    def _calculate_access_log_distance(
        index_log: AccessLog,
        candidate_log: AccessLog,
    ) -> float | None:
        """
        출입 로그 위치 거리 계산
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
