from __future__ import annotations

from typing import Any


def format_task(task: dict[str, Any]) -> str:
    description = task.get("description") or "Без описания"
    recurring = "\n🔁 Повторяется каждый день" if task.get("is_recurring") else ""
    return (
        f"📌 Задача #{task['id']}\n"
        f"📝 Название: {task['title']}\n"
        f"💬 Описание: {description}\n"
        f"📅 Дата: {task['due_date']}\n"
        f"⏰ Время: {task['due_time']}"
        f"{recurring}"
    )
