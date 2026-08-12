"""
프로젝트 예외 정의
"""

from http import HTTPStatus
from typing import Any


class AppError(Exception):
    """
    앱 기본 예외
    """

    def __init__(
        self,
        message: str,
        *,
        error_code: str = "APP_ERROR",
        status_code: int = HTTPStatus.INTERNAL_SERVER_ERROR,
        details: dict[str, Any] | None = None,
    ) -> None:
        """
        예외 초기화
        """

        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.status_code = int(status_code)
        self.details = details or {}


class ConfigurationError(AppError):
    """
    설정 오류
    """

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """
        설정 예외 초기화
        """

        super().__init__(
            message,
            error_code="CONFIGURATION_ERROR",
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            details=details,
        )


class DatabaseConnectionError(AppError):
    """
    DB 연결 오류
    """

    def __init__(
        self,
        message: str = "DB 연결에 실패했습니다.",
        details: dict[str, Any] | None = None,
    ) -> None:
        """
        DB 연결 예외 초기화
        """

        super().__init__(
            message,
            error_code="DATABASE_CONNECTION_ERROR",
            status_code=HTTPStatus.SERVICE_UNAVAILABLE,
            details=details,
        )


class DatabaseTransactionError(AppError):
    """
    DB 트랜잭션 오류
    """

    def __init__(
        self,
        message: str = "DB 트랜잭션 처리에 실패했습니다.",
        details: dict[str, Any] | None = None,
    ) -> None:
        """
        DB 트랜잭션 예외 초기화
        """

        super().__init__(
            message,
            error_code="DATABASE_TRANSACTION_ERROR",
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            details=details,
        )


class ResourceNotFoundError(AppError):
    """
    리소스 없음
    """

    def __init__(
        self,
        resource_name: str,
        resource_id: str | int,
    ) -> None:
        """
        리소스 없음 예외 초기화
        """

        super().__init__(
            f"{resource_name}을 찾을 수 없습니다: {resource_id}",
            error_code="RESOURCE_NOT_FOUND",
            status_code=HTTPStatus.NOT_FOUND,
            details={
                "resource_name": resource_name,
                "resource_id": str(resource_id),
            },
        )


class AgentExecutionError(AppError):
    """
    에이전트 실행 오류
    """

    def __init__(
        self,
        message: str = "에이전트 실행에 실패했습니다.",
        details: dict[str, Any] | None = None,
    ) -> None:
        """
        에이전트 예외 초기화
        """

        super().__init__(
            message,
            error_code="AGENT_EXECUTION_ERROR",
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            details=details,
        )
