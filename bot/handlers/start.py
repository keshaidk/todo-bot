from telegram import Update
from telegram.ext import ContextTypes


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    assert update.message
    await update.message.reply_text(
        "👋 Привет! Я бот для управления задачами.\n\n"
        "📋 Команды:\n"
        "/add — добавить задачу\n"
        "/tasks — список текущих задач\n"
        "/cancel — отменить текущее действие"
    )
