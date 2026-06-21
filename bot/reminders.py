from __future__ import annotations

import logging

from telegram.ext import Application, ContextTypes

from .db import TaskRepository

logger = logging.getLogger(__name__)


async def _send_reminders(context: ContextTypes.DEFAULT_TYPE) -> None:
    repo: TaskRepository = context.bot_data["repo"]
    try:
        tasks = await repo.get_due_soon(within_minutes=30)
    except Exception:
        logger.exception("Ошибка при получении задач для напоминаний")
        return

    for task in tasks:
        try:
            await context.bot.send_message(
                chat_id=task["user_id"],
                text=(
                    f"⏰ Напоминание!\n"
                    f"Задача «{task['title']}» выполняется сегодня в {task['due_time']}."
                ),
            )
        except Exception:
            logger.warning("Не удалось отправить напоминание пользователю %d", task["user_id"])


def setup_reminders(app: Application) -> None:  # type: ignore[type-arg]
    """Регистрирует фоновую задачу проверки дедлайнов каждые 10 минут."""
    job_queue = app.job_queue
    if job_queue is None:
        logger.warning("JobQueue недоступен — напоминания отключены")
        return
    job_queue.run_repeating(_send_reminders, interval=600, first=10)
    logger.info("Напоминания активированы (каждые 10 минут)")
