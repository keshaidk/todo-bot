from __future__ import annotations

import asyncio
import logging
import sys

from telegram.ext import Application

from bot.config import settings
from bot.db import Database, TaskRepository
from bot.handlers import register_all
from bot.reminders import setup_reminders


def setup_logging() -> None:
    logging.basicConfig(
        format="%(asctime)s | %(levelname)-8s | %(name)s: %(message)s",
        level=settings.log_level.upper(),
        stream=sys.stdout,
    )


async def main() -> None:
    setup_logging()
    logger = logging.getLogger(__name__)

    db = Database(settings.db_path)
    await db.connect()

    repo = TaskRepository(db)

    app: Application = (  # type: ignore[type-arg]
        Application.builder()
        .token(settings.bot_token)
        .build()
    )

    # Передаём репозиторий через bot_data — удобно и без глобальных переменных
    app.bot_data["repo"] = repo

    register_all(app)
    setup_reminders(app)

    logger.info("Бот запускается...")
    try:
        await app.initialize()
        await app.start()
        await app.updater.start_polling(drop_pending_updates=True)  # type: ignore[union-attr]
        logger.info("Бот запущен. Нажмите Ctrl+C для остановки.")
        await asyncio.Event().wait()
    finally:
        await app.updater.stop()  # type: ignore[union-attr]
        await app.stop()
        await app.shutdown()
        await db.close()
        logger.info("Бот остановлен.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
