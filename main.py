import logging
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from config import TELEGRAM_BOT_TOKEN, TIMEZONE
from bot import build_app, send_scheduled_digests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> None:
    if not TELEGRAM_BOT_TOKEN:
        logger.error("Set TELEGRAM_BOT_TOKEN in .env")
        return

    app = build_app()

    # Run every minute, check if any subscribers need their digest now
    scheduler = AsyncIOScheduler()

    async def tick() -> None:
        now = datetime.now().strftime("%H:%M")
        await send_scheduled_digests(now, app.bot)

    trigger = CronTrigger(minute="*", timezone=TIMEZONE)
    scheduler.add_job(tick, trigger, id="digest_tick")

    async def on_startup(_app) -> None:
        scheduler.start()
        logger.info(f"Scheduler started (checking every minute, tz={TIMEZONE})")

    async def on_shutdown(_app) -> None:
        if scheduler.running:
            scheduler.shutdown()

    app.post_init = on_startup
    app.post_shutdown = on_shutdown

    logger.info("Bot starting — polling for commands...")
    app.run_polling()


if __name__ == "__main__":
    main()
