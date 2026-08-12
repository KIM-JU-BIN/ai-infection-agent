"""
애플리케이션 전역 로깅 설정
"""

import logging
import sys
from logging import Logger


_LOG_FORMAT = (
    "%(asctime)s | %(levelname)-8s | %(name)s | "
    "%(filename)s:%(lineno)d | %(message)s"
)
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


class SafeFormatter(logging.Formatter):
    """
    안전 포맷터
    """

    def format(self, record: logging.LogRecord) -> str:
        """
        로그 포맷 적용
        """

        try:
            return super().format(record)
        except Exception:
            return f"LOG_FORMAT_ERROR | {record.name} | {record.getMessage()}"


def configure_logging(log_level: int | str = logging.INFO) -> None:
    """
    로깅 초기화
    """

    root_logger = logging.getLogger()

    if isinstance(log_level, str):
        # 파이썬 3.11 이상 권장 방식: getLevelNamesMapping() 사용
        resolved_level = logging.getLevelNamesMapping().get(log_level.upper(), logging.INFO)

        if not isinstance(resolved_level, int):
            resolved_level = logging.INFO
    else:
        resolved_level = log_level

    root_logger.setLevel(resolved_level)

    if root_logger.handlers:
        for handler in root_logger.handlers:
            handler.setLevel(resolved_level)
        return

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(resolved_level)
    stream_handler.setFormatter(
        SafeFormatter(
            fmt=_LOG_FORMAT,
            datefmt=_DATE_FORMAT,
        )
    )

    root_logger.addHandler(stream_handler)


def get_logger(name: str) -> Logger:
    """
    로거 반환
    """

    configure_logging()
    return logging.getLogger(name)
