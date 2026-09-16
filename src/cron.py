import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from .application.scrape_service import scrape_service
from .db import DatabaseUnavailable, ScrapeAlreadyRunning
from .settings import get_settings
from .logger import logger


async def scheduled_scrape() -> None:
    try:
        run = await scrape_service.start()
        logger.info("⏰ Execução agendada iniciada: {}", run.run_id)
    except ScrapeAlreadyRunning:
        logger.warning("⏭️ Execução agendada ignorada: já existe uma execução em andamento")
    except DatabaseUnavailable as error:
        logger.opt(exception=error).error("❌ Execução agendada não iniciada")


async def main() -> None:
    settings = get_settings()
    scheduler = AsyncIOScheduler(timezone=settings.scrape_timezone)
    scheduler.add_job(
        scheduled_scrape,
        CronTrigger.from_crontab(settings.scrape_cron, timezone=settings.scrape_timezone),
        id="property-scrape",
        replace_existing=True,
        coalesce=True,
        max_instances=1,
    )
    scheduler.start()
    logger.info("⏱️ Cron ativo: '{}' ({})", settings.scrape_cron, settings.scrape_timezone)
    try:
        await asyncio.Event().wait()
    finally:
        scheduler.shutdown(wait=False)


if __name__ == "__main__":
    asyncio.run(main())
