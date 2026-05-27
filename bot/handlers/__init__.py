from telegram.ext import Application

from .add_task import build_add_conversation
from .edit_task import build_edit_conversation
from .errors import error_handler
from .tasks_list import complete_task, delete_task, show_tasks
from .start import start_command


def register_all(app: Application) -> None:  # type: ignore[type-arg]
    """Подключает все хэндлеры к приложению."""
    from telegram.ext import CallbackQueryHandler, CommandHandler

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("tasks", show_tasks))
    app.add_handler(build_add_conversation())
    app.add_handler(build_edit_conversation())
    app.add_handler(CallbackQueryHandler(complete_task, pattern=r"^complete:\d+$"))
    app.add_handler(CallbackQueryHandler(delete_task, pattern=r"^delete:\d+$"))
    app.add_error_handler(error_handler)
