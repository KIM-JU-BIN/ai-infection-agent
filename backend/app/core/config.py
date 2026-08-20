"""
앱 설정 관리
환경변수와 .env 값을 읽음
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    전체 설정값
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    PROJECT_NAME: str = Field(
        default="현장 중심 AI 감염관리 조사 에이전트",
        description="프로젝트 이름",
    )

    ENVIRONMENT: Literal["local", "dev", "staging", "prod"] = Field(
        default="local",
        description="실행 환경",
    )

    DEBUG: bool = Field(
        default=False,
        description="디버그 모드",
    )

    VERSION: str = Field(
        default="0.1.0",
        description="앱 버전",
    )

    API_V1_PREFIX: str = Field(
        default="/api/v1",
        description="API v1 경로",
    )

    BACKEND_CORS_ORIGINS: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"],
        description="허용할 프론트 주소",
    )

    DATABASE_URL: PostgresDsn = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5433/infection_control",
        description="비동기 PostgreSQL 주소",
    )

    DB_POOL_SIZE: int = Field(
        default=5,
        ge=1,
        le=50,
        description="기본 DB 연결 수",
    )

    DB_MAX_OVERFLOW: int = Field(
        default=10,
        ge=0,
        le=100,
        description="추가 DB 연결 수",
    )

    DB_POOL_TIMEOUT: int = Field(
        default=30,
        ge=1,
        le=300,
        description="DB 연결 대기 시간",
    )

    DB_POOL_RECYCLE: int = Field(
        default=1800,
        ge=60,
        description="DB 연결 재사용 시간",
    )

    DB_ECHO: bool = Field(
        default=False,
        description="SQL 로그 출력 여부",
    )
    
    OPENAI_API_KEY: str | None = Field(
        default=None,
        description="OpenAI API 키",
    )

    EMBEDDING_MODEL: str = Field(
        default="text-embedding-3-small",
        description="임베딩 모델명",
    )

    EMBEDDING_DIMENSION: int = Field(
        default=1536,
        ge=1,
        description="임베딩 벡터 차원",
    )
    
    CHAT_MODEL: str = Field(
        default="gpt-4o-mini",
        description="채팅 LLM 모델명",
    )



    @field_validator("API_V1_PREFIX")
    @classmethod
    def validate_api_prefix(cls, value: str) -> str:
        """
        API 경로 검증
        """

        if not value.startswith("/"):
            raise ValueError("API_V1_PREFIX는 '/'로 시작해야 합니다.")

        return value.rstrip("/") or "/"

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | list[str]) -> list[str]:
        """
        CORS 주소 파싱
        """

        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]

        if isinstance(value, list):
            return value

        raise TypeError("BACKEND_CORS_ORIGINS는 문자열 또는 리스트여야 합니다.")

    @property
    def is_production(self) -> bool:
        """
        운영 환경 여부
        """

        return self.ENVIRONMENT == "prod"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    설정 객체 캐싱
    """

    return Settings()


settings: Settings = get_settings()

