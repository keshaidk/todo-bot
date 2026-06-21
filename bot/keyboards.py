from __future__ import annotations

from datetime import datetime, timedelta

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

_MONTH_NAMES = [
    "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
    "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь",
]
_WEEKDAYS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]


def _ignore() -> InlineKeyboardButton:
    return InlineKeyboardButton(" ", callback_data="ignore")


def build_calendar(year: int, month: int, prefix: str = "date") -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []

    rows.append([InlineKeyboardButton(f"{_MONTH_NAMES[month - 1]} {year}", callback_data="ignore")])
    rows.append([InlineKeyboardButton(d, callback_data="ignore") for d in _WEEKDAYS])

    first_day = datetime(year, month, 1)
    if month == 12:
        days_in_month = (datetime(year + 1, 1, 1) - timedelta(days=1)).day
    else:
        days_in_month = (datetime(year, month + 1, 1) - timedelta(days=1)).day

    week: list[InlineKeyboardButton] = [_ignore()] * first_day.weekday()
    for day in range(1, days_in_month + 1):
        week.append(InlineKeyboardButton(str(day), callback_data=f"{prefix}:{year}:{month}:{day}"))
        if len(week) == 7:
            rows.append(week)
            week = []
    if week:
        rows.append(week + [_ignore()] * (7 - len(week)))

    prev_y, prev_m = (year, month - 1) if month > 1 else (year - 1, 12)
    next_y, next_m = (year, month + 1) if month < 12 else (year + 1, 1)
    rows.append([
        InlineKeyboardButton("◀️", callback_data=f"calendar_prev:{prev_y}:{prev_m}:{prefix}"),
        InlineKeyboardButton("Сегодня", callback_data=f"calendar_today:{prefix}"),
        InlineKeyboardButton("▶️", callback_data=f"calendar_next:{next_y}:{next_m}:{prefix}"),
    ])
    rows.append([InlineKeyboardButton("Отмена", callback_data=f"cancel_{prefix}")])
    return InlineKeyboardMarkup(rows)


def build_time_keyboard(prefix: str = "time") -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    rows.append([InlineKeyboardButton("— Выберите час —", callback_data="ignore")])

    hour_row: list[InlineKeyboardButton] = []
    for h in range(24):
        hour_row.append(InlineKeyboardButton(f"{h:02d}", callback_data=f"{prefix}_hour:{h}"))
        if len(hour_row) == 6:
            rows.append(hour_row)
            hour_row = []
    if hour_row:
        rows.append(hour_row)

    rows.append([InlineKeyboardButton("— Выберите минуты —", callback_data="ignore")])
    rows.append([
        InlineKeyboardButton(f"{m:02d}", callback_data=f"{prefix}_minute:{m}")
        for m in (0, 15, 30, 45)
    ])
    rows.append([InlineKeyboardButton("Отмена", callback_data=f"cancel_{prefix}")])
    return InlineKeyboardMarkup(rows)


def task_keyboard(task_id: int, is_recurring: bool = False) -> InlineKeyboardMarkup:
    buttons = []
    if not is_recurring:
        buttons.append([InlineKeyboardButton("✅ Завершить", callback_data=f"complete:{task_id}")])
    buttons.append([InlineKeyboardButton("✏️ Редактировать", callback_data=f"edit:{task_id}")])
    buttons.append([InlineKeyboardButton("🗑 Удалить", callback_data=f"delete:{task_id}")])
    return InlineKeyboardMarkup(buttons)


def edit_field_keyboard(task_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Название", callback_data=f"edit_field:{task_id}:title")],
        [InlineKeyboardButton("Описание", callback_data=f"edit_field:{task_id}:description")],
        [InlineKeyboardButton("Дату", callback_data=f"edit_field:{task_id}:due_date")],
        [InlineKeyboardButton("Время", callback_data=f"edit_field:{task_id}:due_time")],
        [InlineKeyboardButton("Отмена", callback_data="cancel_edit")],
    ])
