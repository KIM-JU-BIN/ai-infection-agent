"""
Post-Action Service

미검사 접촉자를 자동 탐지하고 검사 권고 문자를 발송한다
"""

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DatabaseTransactionError
from app.core.logging import get_logger
from app.db.models.post_action import ContactCase
from app.services.sms_service import MockSMSService


logger = get_logger(__name__)


class PostActionService:
    """
    능동적 사후 조치 비즈니스 계층
    """

    def __init__(self, db: AsyncSession) -> None:
        """
        Service 초기화
        """

        self.db = db
        self.sms_service = MockSMSService()

    async def process_untested_contacts(self) -> int:
        """
        미검사 + 문자 미발송 접촉자를 찾아 문자 발송 후 상태를 갱신한다

        Returns:
            문자 발송 성공 건수
        """

        contact_cases = await self._find_untested_and_not_notified_cases()

        if not contact_cases:
            logger.info("[Post-Action] 문자 발송 대상 없음")
            return 0

        sent_count = 0

        for contact_case in contact_cases:
            success = await self.sms_service.send_test_recommendation_sms(
                patient_id=contact_case.patient_id,
                message=self._build_sms_message(contact_case),
            )

            if success:
                contact_case.sms_sent_status = "SENT"
                sent_count += 1
            else:
                contact_case.sms_sent_status = "FAILED"

        try:
            await self.db.commit()
        except SQLAlchemyError as exc:
            await self.db.rollback()
            logger.exception("[Post-Action] 문자 상태 업데이트 실패")
            raise DatabaseTransactionError(
                "문자 발송 상태 업데이트 중 DB 오류가 발생했습니다."
            ) from exc

        logger.info(f"[Post-Action] 문자 발송 처리 완료: {sent_count}건")

        return sent_count

    async def _find_untested_and_not_notified_cases(self) -> list[ContactCase]:
        """
        미검사 + 문자 미발송 접촉자 케이스 조회

        기존 상태값 호환:
        - test_status: PENDING 또는 RECOMMENDED
        - sms_sent_status: NOT_SENT 또는 PENDING
        """

        stmt = (
            select(ContactCase)
            .where(
                ContactCase.test_status.in_(["PENDING", "RECOMMENDED"]),
                ContactCase.sms_sent_status.in_(["NOT_SENT", "PENDING"]),
                ContactCase.risk_level.in_(["HIGH", "MEDIUM"]),
            )
            .order_by(ContactCase.created_at.asc())
        )

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    def _build_sms_message(contact_case: ContactCase) -> str:
        """
        문자 메시지 생성
        """

        return (
            f"{contact_case.disease_type} 접촉자로 분류되어 검사가 권고됩니다. "
            "가까운 검사 장소 또는 병원 안내에 따라 즉시 검사를 받아주세요."
        )
