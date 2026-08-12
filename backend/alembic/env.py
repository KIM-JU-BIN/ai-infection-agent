"""
Alembic 비동기 마이그레이션 설정 (경로 문제 해결 및 타입 감지 적용)
"""

import asyncio
from logging.config import fileConfig
import sys
import os

# 파이썬이 app 폴더를 찾을 수 있도록 루트 경로 강제 추가
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from app.core.config import settings
from app.db.session import Base
import app.db.models  # __init__.py에 정의된 6개 모델 자동 로드

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def get_database_url() -> str:
    """
    DB URL 반환
    """
    return str(settings.DATABASE_URL)

def run_migrations_offline() -> None:
    """
    오프라인 마이그레이션
    """
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,           # 컬럼 타입 변경 감지
        compare_server_default=True, # 디폴트값 변경 감지
    )
    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection: Connection) -> None:
    """
    실제 마이그레이션 실행
    """
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()

async def run_async_migrations() -> None:
    """
    비동기 마이그레이션 실행
    """
    configuration = config.get_section(config.config_ini_section)
    if configuration is None:
        raise RuntimeError("Alembic 설정을 찾을 수 없습니다.")

    configuration["sqlalchemy.url"] = get_database_url()

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()

def run_migrations_online() -> None:
    """
    온라인 마이그레이션
    """
    asyncio.run(run_async_migrations())

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()