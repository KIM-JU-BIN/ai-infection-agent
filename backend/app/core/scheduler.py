"""
백그라운드 스케줄러

FastAPI 서버 실행 중 주기적으로 Post-Action 작업을 수행한다
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.exc import SQLAlchemyError

from app.core.logging import get_logger
from app.db.session import AsyncSessionLocal
from app.services.post_action_service import PostActionService


logger = get_logger(__name__)


scheduler = AsyncIOScheduler()


async def run_post_action_job() -> None:
    """
    미검사 접촉자 문자 발송 Job
    """

    logger.info("[Scheduler] Post-Action Job 시작.")

    async with AsyncSessionLocal() as db:
        try:
            service = PostActionService(db)
            sent_count = await service.process_untested_contacts()

            logger.info(
                f"[Scheduler] Post-Action Job 완료. 문자 발송: {sent_count}건"
            )

        except SQLAlchemyError:
            await db.rollback()
            logger.exception("[Scheduler] DB 오류로 Post-Action Job 실패.")

        except Exception:
            await db.rollback()
            logger.exception("[Scheduler] 알 수 없는 오류로 Post-Action Job 실패.")


def start_scheduler() -> None:
    """
    스케줄러 시작
    """

    if scheduler.running:
        logger.info("[Scheduler] 이미 실행 중")
        return

    scheduler.add_job(
        run_post_action_job,
        trigger=IntervalTrigger(minutes=1),
        id="post_action_job",
        name="미검사 접촉자 문자 발송 Job",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )

    scheduler.start()
    logger.info("[Scheduler] 시작 완료. 1분마다 Post-Action Job 실행.")


def shutdown_scheduler() -> None:
    """
    스케줄러 종료
    """

    if not scheduler.running:
        logger.info("[Scheduler] 이미 종료 상태.")
        return

    scheduler.shutdown(wait=False)
    logger.info("[Scheduler] 종료 완료.")
