from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from ..config import settings
from .connection import Database

logger = logging.getLogger(__name__)

_TZ = ZoneInfo(getattr(settings, "tz", "Europe/Moscow"))
ALLOWED_FIELDS = frozenset({"title", "description", "due_date", "due_time"})


class TaskRepository:
    """CRUD-операции над задачами. Только этот класс знает SQL."""

    def __init__(self, db: Database) -> None:
        self._db = db

    async def add(
        self,
        user_id: int,
        title: str,
        description: str,
        due_date: str,
        due_time: str,
        is_recurring: bool = False,
    ) -> int:
        async with self._db.conn.execute(
            """
            INSERT INTO tasks (user_id, title, description, due_date, due_time, is_recurring)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, title, description, due_date, due_time, int(is_recurring)),
        ) as cur:
            await self._db.conn.commit()
            assert cur.lastrowid is not None
            return int(cur.lastrowid)

    async def get_active(self, user_id: int) -> list[dict[str, Any]]:
        async with self._db.conn.execute(
            """
            SELECT id, title, description, due_date, due_time, is_recurring
            FROM tasks
            WHERE user_id = ? AND is_done = 0
            ORDER BY due_date, due_time, id
            """,
            (user_id,),
        ) as cur:
            rows = await cur.fetchall()
            return [dict(row) for row in rows]

    async def get_by_id(self, task_id: int, user_id: int) -> dict[str, Any] | None:
        async with self._db.conn.execute(
            """
            SELECT id, user_id, title, description, due_date, due_time, is_done, is_recurring
            FROM tasks
            WHERE id = ? AND user_id = ?
            """,
            (task_id, user_id),
        ) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None

    async def mark_done(self, task_id: int, user_id: int) -> bool:
        async with self._db.conn.execute(
            """
            UPDATE tasks
            SET is_done = 1,
                completed_at = strftime('%Y-%m-%dT%H:%M:%S', 'now')
            WHERE id = ? AND user_id = ? AND is_done = 0
            """,
            (task_id, user_id),
        ) as cur:
            await self._db.conn.commit()
            return cur.rowcount > 0

    async def delete(self, task_id: int, user_id: int) -> bool:
        async with self._db.conn.execute(
            "DELETE FROM tasks WHERE id = ? AND user_id = ?",
            (task_id, user_id),
        ) as cur:
            await self._db.conn.commit()
            return cur.rowcount > 0

    async def update_field(
        self, task_id: int, user_id: int, field: str, value: str
    ) -> bool:
        if field not in ALLOWED_FIELDS:
            raise ValueError(f"Поле '{field}' недоступно для редактирования")
        
        # Use parameterized queries with whitelist to prevent SQL injection
        field_mapping = {
            "title": "title = ?",
            "description": "description = ?",
            "due_date": "due_date = ?",
            "due_time": "due_time = ?",
        }
        
        set_clause = field_mapping[field]
        async with self._db.conn.execute(
            f"UPDATE tasks SET {set_clause} WHERE id = ? AND user_id = ? AND is_done = 0",
            (value, task_id, user_id),
        ) as cur:
            await self._db.conn.commit()
            return cur.rowcount > 0

    async def get_due_soon(self, within_minutes: int = 30) -> list[dict[str, Any]]:
        """Возвращает задачи, дедлайн которых наступит в ближайшие N минут."""
        async with self._db.conn.execute(
            """
            SELECT id, user_id, title, due_date, due_time, is_recurring
            FROM tasks
            WHERE is_done = 0
            """
        ) as cur:
            rows = await cur.fetchall()

        now = datetime.now(tz=_TZ)
        due_tasks: list[dict[str, Any]] = []
        for row in rows:
            try:
                if row["is_recurring"]:
                    due_dt = datetime.strptime(row["due_time"], "%H:%M").replace(
                        year=now.year,
                        month=now.month,
                        day=now.day,
                        tzinfo=_TZ,
                    )
                    if due_dt < now:
                        due_dt += timedelta(days=1)
                else:
                    due_dt = datetime.strptime(
                        f"{row['due_date']} {row['due_time']}", "%Y-%m-%d %H:%M"
                    ).replace(tzinfo=_TZ)
            except (ValueError, TypeError):
                continue

            delta = (due_dt - now).total_seconds()
            if 0 <= delta <= within_minutes * 60:
                due_tasks.append(dict(row))

        return due_tasks
