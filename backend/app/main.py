"""
FastAPI 진입점
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.api.v1.endpoints import patients
from app.core.config import settings
from app.core.exceptions import AppError, DatabaseConnectionError
from app.core.logging import configure_logging, get_logger
from app.db.session import check_database_connection, close_database_connection


configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    서버 시작/종료 처리
    """

    logger.info(
        "앱 시작.",
        extra={
            "project_name": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "environment": settings.ENVIRONMENT,
        },
    )

    try:
        await check_database_connection()
        app.state.is_ready = True

        logger.info("앱 시작 완료.")

        yield

    except DatabaseConnectionError:
        app.state.is_ready = False
        logger.exception("DB 연결 실패로 앱 시작 중단.")
        raise

    except Exception:
        app.state.is_ready = False
        logger.exception("앱 시작 중 알 수 없는 오류.")
        raise

    finally:
        app.state.is_ready = False

        try:
            await close_database_connection()
            logger.info("앱 종료 완료.")

        except Exception:
            logger.exception("앱 종료 중 오류 발생.")


def create_app() -> FastAPI:
    """
    FastAPI 앱 생성
    """

    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description=(
            "현장 중심 AI 감염관리 조사 에이전트 백엔드 API. "
            "FastAPI, PostgreSQL, pgvector, LangGraph 기반 서버입니다."
        ),
        debug=settings.DEBUG,
        lifespan=lifespan,
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        openapi_url="/openapi.json" if not settings.is_production else None,
    )

    configure_middlewares(app)
    configure_exception_handlers(app)
    configure_routes(app)

    return app


def configure_middlewares(app: FastAPI) -> None:
    """
    미들웨어 설정
    """

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    logger.info("CORS 설정 완료.")


def configure_exception_handlers(app: FastAPI) -> None:
    """
    예외 처리 등록
    """

    @app.exception_handler(AppError)
    async def app_error_handler(
        request: Request,
        exc: AppError,
    ) -> JSONResponse:
        """
        앱 예외 처리
        """

        logger.warning(
            "앱 예외 발생.",
            extra={
                "path": request.url.path,
                "method": request.method,
                "error_code": exc.error_code,
                "details": exc.details,
            },
        )

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error_code": exc.error_code,
                "message": exc.message,
                "details": exc.details,
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        """
        요청 검증 오류 처리
        """

        logger.warning(
            "요청 검증 실패.",
            extra={
                "path": request.url.path,
                "method": request.method,
                "errors": exc.errors(),
            },
        )

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "success": False,
                "error_code": "VALIDATION_ERROR",
                "message": "요청 데이터 형식이 올바르지 않습니다.",
                "details": exc.errors(),
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        """
        미처리 예외 처리
        """

        logger.exception(
            "서버 내부 오류.",
            extra={
                "path": request.url.path,
                "method": request.method,
            },
        )

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error_code": "INTERNAL_SERVER_ERROR",
                "message": "서버 내부 오류가 발생했습니다.",
            },
        )


def configure_routes(app: FastAPI) -> None:
    """
    라우트 등록
    """

    app.include_router(
        api_router,
        prefix=settings.API_V1_PREFIX,
    )
    
    app.include_router(
        patients.router, 
        prefix=f"{settings.API_V1_PREFIX}/patients", 
        tags=["환자 관리"]
    )

    @app.get(
        "/",
        status_code=status.HTTP_200_OK,
        summary="기본 확인",
    )
    async def root() -> dict[str, str]:
        """
        서버 기본 정보.
        """

        return {
            "service": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "status": "running",
        }


app: FastAPI = create_app()


