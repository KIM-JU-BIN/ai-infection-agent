"""
환자 Service
비즈니스 로직만 담당
"""

from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ResourceNotFoundError
from app.db.models.patient import Patient
from app.repositories.patient_repository import PatientRepository
from app.schemas.patient import PatientCreate, PatientUpdate


class PatientService:
    """
    환자 비즈니스 계층
    """

    def __init__(self, db: AsyncSession) -> None:
        """
        Service 초기화
        """

        self.repository = PatientRepository(db)

    async def get_patient(self, patient_id: int) -> Patient:
        """
        환자 단건 조회
        """

        patient = await self.repository.get_by_id(patient_id)

        if patient is None:
            raise ResourceNotFoundError("Patient", patient_id)

        return patient

    async def get_patient_by_identifier(self, patient_identifier: str) -> Patient:
        """
        환자 식별자 조회
        """

        patient = await self.repository.get_by_identifier(patient_identifier)

        if patient is None:
            raise ResourceNotFoundError("Patient", patient_identifier)

        return patient

    async def list_patients(
        self,
        *,
        offset: int = 0,
        limit: int = 50,
    ) -> Sequence[Patient]:
        """
        환자 목록 조회
        """

        safe_offset = max(offset, 0)
        safe_limit = min(max(limit, 1), 100)

        return await self.repository.list_patients(
            offset=safe_offset,
            limit=safe_limit,
        )

    async def create_patient(self, patient_in: PatientCreate) -> Patient:
        """
        환자 생성
        """

        return await self.repository.create(patient_in)

    async def update_patient(
        self,
        patient_id: int,
        patient_in: PatientUpdate,
    ) -> Patient:
        """
        환자 수정
        """

        patient = await self.get_patient(patient_id)
        return await self.repository.update(patient, patient_in)

    async def delete_patient(self, patient_id: int) -> None:
        """
        환자 삭제
        """

        patient = await self.get_patient(patient_id)
        await self.repository.delete(patient)
