"""
비동기 DB 세션 관리
"""

from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncAttrs,
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings
from app.core.exceptions import DatabaseConnectionError, DatabaseTransactionError
from app.core.logging import get_logger


logger = get_logger(__name__)


class Base(AsyncAttrs, DeclarativeBase):
    """
    모든 ORM 모델의 기본 클래스
    """

    pass


engine: AsyncEngine = create_async_engine(
    str(settings.DATABASE_URL),
    echo=settings.DB_ECHO,
    pool_pre_ping=True,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    pool_recycle=settings.DB_POOL_RECYCLE,
    future=True,
)


AsyncSessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    DB 세션 주입
    """

    async with AsyncSessionLocal() as session:
        try:
            yield session

        except Exception as exc:
            logger.exception("DB 세션 오류. 롤백을 시도합니다.")

            try:
                await session.rollback()
            except SQLAlchemyError as rollback_exc:
                logger.exception("DB 롤백 실패.")
                raise DatabaseTransactionError(
                    "DB 트랜잭션 롤백에 실패했습니다."
                ) from rollback_exc

            raise exc

        finally:
            await session.close()


async def check_database_connection() -> None:
    """
    DB 연결 확인
    """

    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))

        logger.info("DB 연결 확인 성공.")

    except SQLAlchemyError as exc:
        logger.exception("DB 연결 확인 실패.")
        raise DatabaseConnectionError() from exc


async def close_database_connection() -> None:
    """
    DB 연결 종료
    """

    try:
        await engine.dispose()
        logger.info("DB 엔진 종료 완료.")

    except SQLAlchemyError:
        logger.exception("DB 엔진 종료 실패.")
        raise

