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
from ..keyboards import build_calendar, build_time_keyboard, edit_field_keyboard, task_keyboard
from ..utils.datetime_helpers import is_valid_date, is_valid_time, now_local
from ..utils.formatters import format_task

logger = logging.getLogger(__name__)

EDIT_CHOOSE_FIELD, EDIT_VALUE = range(2)

FIELD_LABELS = {
    "title": "новое название",
    "description": "новое описание (или «-» для пустого)",
}


def _repo(context: ContextTypes.DEFAULT_TYPE) -> TaskRepository:
    return context.bot_data["repo"]


async def edit_task(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    assert query
    await query.answer()
    task_id = int((query.data or "").split(":")[1])
    task = await _repo(context).get_by_id(task_id, query.from_user.id)

    if not task or task["is_done"]:
        await query.edit_message_text("Задача не найдена или уже завершена.")
        return ConversationHandler.END

    context.user_data["edit_id"] = task_id
    await query.edit_message_text(
        f"Что изменить?\n\n{format_task(task)}",
        reply_markup=edit_field_keyboard(task_id),
    )
    return EDIT_CHOOSE_FIELD


async def choose_field(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    assert query
    await query.answer()
    _, task_id_raw, field = (query.data or "").split(":")
    task_id = int(task_id_raw)
    context.user_data["edit_id"] = task_id
    context.user_data["edit_field"] = field

    if field == "due_date":
        today = now_local()
        await query.edit_message_text(
            "📅 Выберите новую дату:",
            reply_markup=build_calendar(today.year, today.month, "edit_due_date"),
        )
    elif field == "due_time":
        await query.edit_message_text(
            "⏰ Выберите новое время:",
            reply_markup=build_time_keyboard("edit_due_time"),
        )
    else:
        await query.edit_message_text(f"Введите {FIELD_LABELS[field]}:")
    return EDIT_VALUE


async def cancel_edit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    assert query
    await query.answer()
    context.user_data.pop("edit_id", None)
    context.user_data.pop("edit_field", None)
    await query.edit_message_text("Редактирование отменено.")
    return ConversationHandler.END


async def edit_value_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    assert query
    await query.answer()

    data = (query.data or "").split(":")
    task_id: int = context.user_data["edit_id"]
    field: str = context.user_data["edit_field"]
    user_id = query.from_user.id

    if data[0] == "ignore":
        return EDIT_VALUE

    if data[0] in ("cancel_edit_due_date", "cancel_edit_due_time"):
        await query.edit_message_text("Редактирование отменено.")
        context.user_data.pop("edit_id", None)
        context.user_data.pop("edit_field", None)
        return ConversationHandler.END

    new_value: str | None = None

    if field == "due_date":
        if data[0] in ("calendar_prev", "calendar_next"):
            year, month, prefix = int(data[1]), int(data[2]), data[3]
            await query.edit_message_reply_markup(build_calendar(year, month, prefix))
            return EDIT_VALUE
        if data[0] == "calendar_today":
            today = now_local()
            new_value = today.strftime("%Y-%m-%d")
        elif data[0] == "edit_due_date":
            new_value = f"{data[1]}-{int(data[2]):02d}-{int(data[3]):02d}"

    elif field == "due_time":
        if data[0] == "edit_due_time_hour":
            context.user_data["_hour"] = int(data[1])
            await query.edit_message_text(
                f"Час: {int(data[1]):02d}\nВыберите минуты:",
                reply_markup=build_time_keyboard("edit_due_time"),
            )
            return EDIT_VALUE
        if data[0] == "edit_due_time_minute":
            hour = context.user_data.pop("_hour", None)
            if hour is None:
                await query.edit_message_text("Сначала выберите час.")
                return EDIT_VALUE
            new_value = f"{hour:02d}:{int(data[1]):02d}"

    if new_value is None:
        return EDIT_VALUE

    # Validate date and time fields
    if field == "due_date" and not is_valid_date(new_value):
        await query.edit_message_text("Неверный формат даты. Попробуйте снова.")
        return EDIT_VALUE
    
    if field == "due_time" and not is_valid_time(new_value):
        await query.edit_message_text("Неверный формат времени. Попробуйте снова.")
        return EDIT_VALUE

    return await _apply_edit(query, context, task_id, user_id, field, new_value)


async def save_text_edit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    assert update.message
    task_id: int = context.user_data["edit_id"]
    field: str = context.user_data["edit_field"]
    value = (update.message.text or "").strip()
    user_id = update.effective_user.id  # type: ignore[union-attr]

    if field == "title" and not value:
        await update.message.reply_text("Название не может быть пустым. Введите снова:")
        return EDIT_VALUE

    if field == "description" and value == "-":
        value = ""

    repo = _repo(context)
    try:
        updated = await repo.update_field(task_id, user_id, field, value)
        task = await repo.get_by_id(task_id, user_id)
    except Exception:
        logger.exception("Ошибка при сохранении поля %s", field)
        await update.message.reply_text("Не удалось сохранить изменения.")
        return ConversationHandler.END
    finally:
        context.user_data.pop("edit_id", None)
        context.user_data.pop("edit_field", None)

    if not updated or not task:
        await update.message.reply_text("Задача не найдена или уже завершена.")
        return ConversationHandler.END

    await update.message.reply_text(
        "✅ Изменения сохранены:\n\n" + format_task(task),
        reply_markup=task_keyboard(task_id),
    )
    return ConversationHandler.END


async def _apply_edit(query, context, task_id, user_id, field, new_value) -> int:  # type: ignore
    repo = _repo(context)
    try:
        updated = await repo.update_field(task_id, user_id, field, new_value)
        task = await repo.get_by_id(task_id, user_id)
    except Exception:
        logger.exception("Ошибка при сохранении поля %s", field)
        await query.edit_message_text("Не удалось сохранить изменения.")
        return ConversationHandler.END
    finally:
        context.user_data.pop("edit_id", None)
        context.user_data.pop("edit_field", None)

    if not updated or not task:
        await query.edit_message_text("Задача не найдена или уже завершена.")
        return ConversationHandler.END

    await query.edit_message_text(
        "✅ Изменения сохранены:\n\n" + format_task(task),
        reply_markup=task_keyboard(task_id),
    )
    return ConversationHandler.END


def build_edit_conversation() -> ConversationHandler:  # type: ignore[type-arg]
    return ConversationHandler(
        entry_points=[CallbackQueryHandler(edit_task, pattern=r"^edit:\d+$")],
        states={
            EDIT_CHOOSE_FIELD: [
                CallbackQueryHandler(
                    choose_field,
                    pattern=r"^edit_field:\d+:(title|description|due_date|due_time)$",
                ),
                CallbackQueryHandler(cancel_edit, pattern=r"^cancel_edit$"),
            ],
            EDIT_VALUE: [
                CallbackQueryHandler(edit_value_callback),
                MessageHandler(filters.TEXT & ~filters.COMMAND, save_text_edit),
            ],
        },
        fallbacks=[CommandHandler("cancel", _cancel)],
    )


async def _cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    assert update.message
    context.user_data.pop("edit_id", None)
    context.user_data.pop("edit_field", None)
    await update.message.reply_text("Действие отменено.")
    return ConversationHandler.END
