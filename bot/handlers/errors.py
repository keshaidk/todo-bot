from __future__ import annotations

import logging

from telegram import Update
from telegram.error import TelegramError
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Логирует все необработанные исключения и уведомляет пользователя."""
    logger.exception("Необработанная ошибка", exc_info=context.error)

    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "⚠️ Произошла ошибка. Попробуйте ещё раз или используйте /cancel."
            )
        except TelegramError:
            logger.exception("Не удалось отправить сообщение об ошибке пользователю")
