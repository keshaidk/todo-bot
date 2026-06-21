from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from ..db import TaskRepository
from ..keyboards import build_calendar, build_time_keyboard
from ..utils.datetime_helpers import is_valid_date, is_valid_time, now_local

logger = logging.getLogger(__name__)

ADD_TITLE, ADD_DESCRIPTION, ADD_REPEAT, ADD_DATE, ADD_TIME = range(5)

_KEY = "new_task"


def _repo(context: ContextTypes.DEFAULT_TYPE) -> TaskRepository:
    return context.bot_data["repo"]


async def add_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    assert update.message
    context.user_data[_KEY] = {}
    await update.message.reply_text("✏️ Введите название задачи:")
    return ADD_TITLE


async def add_title(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    assert update.message
    title = (update.message.text or "").strip()
    if not title:
        await update.message.reply_text("Название не может быть пустым. Попробуйте ещё раз:")
        return ADD_TITLE
    context.user_data[_KEY]["title"] = title
    await update.message.reply_text(
        "📝 Введите описание задачи.\nЕсли описание не нужно — отправьте «-»:"
    )
    return ADD_DESCRIPTION


async def add_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    assert update.message
    raw = (update.message.text or "").strip()
    context.user_data[_KEY]["description"] = "" if raw == "-" else raw
    await update.message.reply_text(
        "🔁 Напоминать каждый день в одно и то же время? Ответьте Да или Нет."
    )
    return ADD_REPEAT


async def add_repeat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    assert update.message
    text = (update.message.text or "").strip().lower()
    if text in ("да", "д", "yes", "y"):
        context.user_data[_KEY]["is_recurring"] = True
    elif text in ("нет", "н", "no", "n"):
        context.user_data[_KEY]["is_recurring"] = False
    else:
        await update.message.reply_text("Пожалуйста, ответьте 'Да' или 'Нет'.")
        return ADD_REPEAT

    today = now_local()
    await update.message.reply_text(
        "📅 Укажите дату начала задачи:",
        reply_markup=build_calendar(today.year, today.month),
    )
    return ADD_DATE


async def add_date_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    assert query
    await query.answer()
    data = query.data or ""

    if data == "ignore":
        return ADD_DATE

    parts = data.split(":")

    if parts[0] in ("calendar_prev", "calendar_next"):
        year, month, prefix = int(parts[1]), int(parts[2]), parts[3]
        await query.edit_message_reply_markup(build_calendar(year, month, prefix))
        return ADD_DATE

    if parts[0] == "calendar_today":
        today = now_local()
        due_date = today.strftime("%Y-%m-%d")
        context.user_data[_KEY]["due_date"] = due_date
        await query.edit_message_text(
            f"✅ Дата: {due_date}\n⏰ Выберите время:",
            reply_markup=build_time_keyboard(),
        )
        return ADD_TIME

    if parts[0] == "cancel_date":
        await query.edit_message_text("Отменено. Используйте /add для повторного добавления.")
        context.user_data.pop(_KEY, None)
        return ConversationHandler.END

    if parts[0] == "date":
        year, month, day = int(parts[1]), int(parts[2]), int(parts[3])
        due_date = f"{year}-{month:02d}-{day:02d}"
        context.user_data[_KEY]["due_date"] = due_date
        await query.edit_message_text(
            f"✅ Дата: {due_date}\n⏰ Выберите время:",
            reply_markup=build_time_keyboard(),
        )
        return ADD_TIME

    return ADD_DATE


async def add_time_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    assert query
    await query.answer()
    data = query.data or ""

    if data == "ignore":
        return ADD_TIME

    parts = data.split(":")

    if parts[0] == "cancel_time":
        await query.edit_message_text("Отменено. Используйте /add.")
        context.user_data.pop(_KEY, None)
        return ConversationHandler.END

    if parts[0] == "time_hour":
        context.user_data["_hour"] = int(parts[1])
        await query.edit_message_text(
            f"Час: {int(parts[1]):02d}\nВыберите минуты:",
            reply_markup=build_time_keyboard(),
        )
        return ADD_TIME

    if parts[0] == "time_minute":
        hour = context.user_data.pop("_hour", None)
        if hour is None:
            await query.edit_message_text("Сначала выберите час.")
            return ADD_TIME

        due_time = f"{hour:02d}:{int(parts[1]):02d}"
        task_data = context.user_data.pop(_KEY, {})

        # Validate date and time
        if not is_valid_date(task_data["due_date"]):
            await query.edit_message_text("Неверный формат даты. Попробуйте /add ещё раз.")
            return ConversationHandler.END
        
        if not is_valid_time(due_time):
            await query.edit_message_text("Неверный формат времени. Попробуйте /add ещё раз.")
            return ConversationHandler.END

        try:
            task_id = await _repo(context).add(
                user_id=query.from_user.id,
                title=task_data["title"],
                description=task_data.get("description", ""),
                due_date=task_data["due_date"],
                due_time=due_time,
                is_recurring=task_data.get("is_recurring", False),
            )
        except Exception:
            logger.exception("Ошибка при сохранении задачи")
            await query.edit_message_text("Не удалось сохранить задачу. Попробуйте /add ещё раз.")
            return ConversationHandler.END

        await query.edit_message_text(
            f"✅ Задача #{task_id} сохранена!\n"
            f"📅 {task_data['due_date']} ⏰ {due_time}\n"
            + ("🔁 Напоминание будет приходить каждый день.\n" if task_data.get("is_recurring") else "")
            + "\nПосмотреть список: /tasks"
        )
        return ConversationHandler.END

    return ADD_TIME


def build_add_conversation() -> ConversationHandler:  # type: ignore[type-arg]
    return ConversationHandler(
        entry_points=[CommandHandler("add", add_start)],
        states={
            ADD_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_title)],
            ADD_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_description)],
            ADD_REPEAT: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_repeat)],
            ADD_DATE: [CallbackQueryHandler(add_date_callback)],
            ADD_TIME: [CallbackQueryHandler(add_time_callback)],
        },
        fallbacks=[CommandHandler("cancel", _cancel)],
    )


async def _cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    assert update.message
    context.user_data.pop(_KEY, None)
    context.user_data.pop("_hour", None)
    await update.message.reply_text("Действие отменено.")
    return ConversationHandler.END
