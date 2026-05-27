import pytest
import pytest_asyncio

from bot.db.connection import Database
from bot.db.repository import TaskRepository


@pytest_asyncio.fixture
async def db():
    """Временная in-memory база данных для каждого теста."""
    database = Database(":memory:")
    await database.connect()
    yield database
    await database.close()


@pytest_asyncio.fixture
async def repo(db: Database) -> TaskRepository:
    return TaskRepository(db)
