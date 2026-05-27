from __future__ import annotations

import logging
from pathlib import Path

import aiosqlite

logger = logging.getLogger(__name__)

_SCHEMA = """
PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS tasks (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL,
    title       TEXT    NOT NULL,
    description TEXT    NOT NULL DEFAULT '',
    due_date    TEXT    NOT NULL,
    due_time    TEXT    NOT NULL,
    is_done     INTEGER NOT NULL DEFAULT 0,
    created_at  TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S', 'now')),
    completed_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_tasks_user_done
    ON tasks (user_id, is_done, due_date, due_time);
"""


class Database:
    """Обёртка над aiosqlite с одним долгоживущим соединением."""

    def __init__(self, db_path: str) -> None:
        self._path = db_path
        self._conn: aiosqlite.Connection | None = None

    async def connect(self) -> None:
        Path(self._path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = await aiosqlite.connect(self._path)
        self._conn.row_factory = aiosqlite.Row
        await self._conn.executescript(_SCHEMA)
        await self._conn.commit()
        await self._migrate()
        await self._conn.commit()
        logger.info("Database connected: %s", self._path)

    async def _migrate(self) -> None:
        async with self._conn.execute("PRAGMA table_info(tasks)") as cur:
            columns = await cur.fetchall()
        if not any(column[1] == "is_recurring" for column in columns):
            await self._conn.execute(
                "ALTER TABLE tasks ADD COLUMN is_recurring INTEGER NOT NULL DEFAULT 0"
            )

    async def close(self) -> None:
        if self._conn:
            await self._conn.close()
            self._conn = None
            logger.info("Database connection closed")

    @property
    def conn(self) -> aiosqlite.Connection:
        if self._conn is None:
            raise RuntimeError("Database is not connected. Call await db.connect() first.")
        return self._conn
