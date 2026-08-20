"""
Mock SMS Service

실제 문자 API 대신 서버 로그에 문자 발송 결과를 남긴다
"""

from app.core.logging import get_logger


logger = get_logger(__name__)


class MockSMSService:
    """
    가짜 문자 발송 서비스

    실제 운영에서는 NHN Cloud, 알리고, Twilio, 카카오 알림톡 등으로 교체 가능하다
    """

    async def send_test_recommendation_sms(
        self,
        *,
        patient_id: int,
        message: str | None = None,
    ) -> bool:
        """
        검사 권고 문자 발송

        Args:
            patient_id: 문자 대상 환자 ID
            message: 발송할 메시지. 없으면 기본 문구 사용

        Returns:
            발송 성공 여부
        """

        sms_message = message or "즉시 코로나 검사를 받아주세요."

        logger.info(
            f"[SMS 전송 성공] 대상자 ID: {patient_id} - {sms_message}"
        )

        return True
