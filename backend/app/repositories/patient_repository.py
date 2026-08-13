"""
환자 Repository
DB 접근만 담당
"""

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DatabaseTransactionError
from app.core.logging import get_logger
from app.db.models.patient import Patient
from app.schemas.patient import PatientCreate, PatientUpdate


logger = get_logger(__name__)


class PatientRepository:
    """
    환자 DB 접근 계층
    """

    def __init__(self, db: AsyncSession) -> None:
        """
        Repository 초기화
        """

        self.db = db

    async def get_by_id(self, patient_id: int) -> Patient | None:
        """
        ID로 환자 조회
        """

        stmt = select(Patient).where(Patient.id == patient_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_identifier(self, patient_identifier: str) -> Patient | None:
        """
        환자 식별자로 조회
        """

        stmt = select(Patient).where(
            Patient.patient_identifier == patient_identifier,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_patients(
        self,
        *,
        offset: int = 0,
        limit: int = 50,
    ) -> Sequence[Patient]:
        """
        환자 목록 조회
        """

        stmt = (
            select(Patient)
            .order_by(Patient.id.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def create(self, patient_in: PatientCreate) -> Patient:
        """
        환자 생성
        """

        patient = Patient(**patient_in.model_dump())

        try:
            self.db.add(patient)
            await self.db.flush()
            await self.db.refresh(patient)
            return patient

        except SQLAlchemyError as exc:
            logger.exception("환자 생성 실패.")
            raise DatabaseTransactionError("환자 생성 중 DB 오류가 발생했습니다.") from exc

    async def update(
        self,
        patient: Patient,
        patient_in: PatientUpdate,
    ) -> Patient:
        """
        환자 수정
        """

        update_data = patient_in.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(patient, field, value)

        try:
            await self.db.flush()
            await self.db.refresh(patient)
            return patient

        except SQLAlchemyError as exc:
            logger.exception("환자 수정 실패.")
            raise DatabaseTransactionError("환자 수정 중 DB 오류가 발생했습니다.") from exc

    async def delete(self, patient: Patient) -> None:
        """
        환자 삭제
        """

        try:
            await self.db.delete(patient)
            await self.db.flush()

        except SQLAlchemyError as exc:
            logger.exception("환자 삭제 실패.")
            raise DatabaseTransactionError("환자 삭제 중 DB 오류가 발생했습니다.") from exc
