from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import ContextTypes

from ..db import TaskRepository
from ..keyboards import task_keyboard
from ..utils.formatters import format_task

logger = logging.getLogger(__name__)


def _repo(context: ContextTypes.DEFAULT_TYPE) -> TaskRepository:
    return context.bot_data["repo"]


async def show_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    assert update.message
    try:
        tasks = await _repo(context).get_active(update.effective_user.id)  # type: ignore[union-attr]
    except Exception:
        logger.exception("Ошибка при получении задач")
        await update.message.reply_text("Не удалось получить задачи. Попробуйте позже.")
        return

    if not tasks:
        await update.message.reply_text("У вас нет текущих задач. Добавить новую: /add")
        return

    await update.message.reply_text("📋 Ваши текущие задачи:")
    for task in tasks:
        await update.message.reply_text(
            format_task(task), reply_markup=task_keyboard(task["id"], bool(task.get("is_recurring")))
        )


async def complete_task(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    assert query
    await query.answer()

    task_id = int((query.data or "").split(":")[1])
    user_id = query.from_user.id
    repo = _repo(context)

    try:
        task = await repo.get_by_id(task_id, user_id)
        if not task or task["is_done"]:
            await query.edit_message_text("Задача не найдена или уже завершена.")
            return
        if task.get("is_recurring"):
            await query.edit_message_text(
                "Эта задача повторяется ежедневно. Удалите её, если больше не нужно."
            )
            return
        if await repo.mark_done(task_id, user_id):
            await query.edit_message_text(f"✅ Задача завершена: {task['title']}")
        else:
            await query.edit_message_text("Не удалось завершить задачу.")
    except Exception:
        logger.exception("Ошибка при завершении задачи %d", task_id)
        await query.message.reply_text("Произошла ошибка. Попробуйте позже.")  # type: ignore[union-attr]


async def delete_task(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    assert query
    await query.answer()

    task_id = int((query.data or "").split(":")[1])
    user_id = query.from_user.id
    repo = _repo(context)

    try:
        task = await repo.get_by_id(task_id, user_id)
        if not task:
            await query.edit_message_text("Задача не найдена.")
            return
        if await repo.delete(task_id, user_id):
            await query.edit_message_text(f"🗑 Задача удалена: {task['title']}")
        else:
            await query.edit_message_text("Не удалось удалить задачу.")
    except Exception:
        logger.exception("Ошибка при удалении задачи %d", task_id)
        await query.message.reply_text("Произошла ошибка. Попробуйте позже.")  # type: ignore[union-attr]
