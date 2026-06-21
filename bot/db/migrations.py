from __future__ import annotations

import logging
from typing import Callable

from .connection import Database

logger = logging.getLogger(__name__)

# Migration functions
async def migration_001_add_is_recurring(db: Database) -> None:
    """Add is_recurring column to tasks table."""
    async with db.conn.execute("PRAGMA table_info(tasks)") as cur:
        columns = await cur.fetchall()
    if not any(column[1] == "is_recurring" for column in columns):
        await db.conn.execute(
            "ALTER TABLE tasks ADD COLUMN is_recurring INTEGER NOT NULL DEFAULT 0"
        )
        logger.info("Migration 001: Added is_recurring column")


# Migration registry
_MIGRATIONS: list[tuple[int, str, Callable[[Database], None]]] = [
    (1, "add_is_recurring", migration_001_add_is_recurring),
]


async def run_migrations(db: Database) -> None:
    """Run all pending migrations."""
    # Create migrations table if not exists
    await db.conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            applied_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S', 'now'))
        )
        """
    )
    
    # Get applied migrations
    async with db.conn.execute("SELECT version FROM schema_migrations ORDER BY version") as cur:
        applied = {row[0] for row in await cur.fetchall()}
    
    # Run pending migrations
    for version, name, migration_func in _MIGRATIONS:
        if version not in applied:
            logger.info(f"Running migration {version}: {name}")
            try:
                await migration_func(db)
                await db.conn.execute(
                    "INSERT INTO schema_migrations (version, name) VALUES (?, ?)",
                    (version, name)
                )
                await db.conn.commit()
                logger.info(f"Migration {version} completed successfully")
            except Exception:
                logger.exception(f"Migration {version} failed")
                raise
