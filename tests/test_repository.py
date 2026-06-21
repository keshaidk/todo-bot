from datetime import timedelta

import pytest

from bot.db.repository import TaskRepository
from bot.utils.datetime_helpers import now_local

USER_ID = 42


@pytest.mark.asyncio
async def test_add_and_get_active(repo: TaskRepository):
    task_id = await repo.add(USER_ID, "Купить молоко", "", "2025-12-01", "10:00")
    tasks = await repo.get_active(USER_ID)
    assert len(tasks) == 1
    assert tasks[0]["id"] == task_id
    assert tasks[0]["title"] == "Купить молоко"


@pytest.mark.asyncio
async def test_mark_done(repo: TaskRepository):
    task_id = await repo.add(USER_ID, "Задача 1", "", "2025-12-01", "10:00")
    result = await repo.mark_done(task_id, USER_ID)
    assert result is True
    tasks = await repo.get_active(USER_ID)
    assert len(tasks) == 0


@pytest.mark.asyncio
async def test_mark_done_twice(repo: TaskRepository):
    task_id = await repo.add(USER_ID, "Задача 2", "", "2025-12-01", "10:00")
    await repo.mark_done(task_id, USER_ID)
    result = await repo.mark_done(task_id, USER_ID)
    assert result is False


@pytest.mark.asyncio
async def test_delete(repo: TaskRepository):
    task_id = await repo.add(USER_ID, "Удалить меня", "", "2025-12-01", "10:00")
    result = await repo.delete(task_id, USER_ID)
    assert result is True
    task = await repo.get_by_id(task_id, USER_ID)
    assert task is None


@pytest.mark.asyncio
async def test_update_field(repo: TaskRepository):
    task_id = await repo.add(USER_ID, "Старый заголовок", "", "2025-12-01", "10:00")
    result = await repo.update_field(task_id, USER_ID, "title", "Новый заголовок")
    assert result is True
    task = await repo.get_by_id(task_id, USER_ID)
    assert task is not None
    assert task["title"] == "Новый заголовок"


@pytest.mark.asyncio
async def test_update_forbidden_field(repo: TaskRepository):
    task_id = await repo.add(USER_ID, "Задача", "", "2025-12-01", "10:00")
    with pytest.raises(ValueError, match="недоступно"):
        await repo.update_field(task_id, USER_ID, "is_done", "1")


@pytest.mark.asyncio
async def test_other_user_cannot_access(repo: TaskRepository):
    task_id = await repo.add(USER_ID, "Чужая задача", "", "2025-12-01", "10:00")
    task = await repo.get_by_id(task_id, user_id=999)
    assert task is None


@pytest.mark.asyncio
async def test_tasks_sorted_by_date(repo: TaskRepository):
    await repo.add(USER_ID, "Поздняя", "", "2025-12-31", "23:59")
    await repo.add(USER_ID, "Ранняя", "", "2025-01-01", "00:00")
    tasks = await repo.get_active(USER_ID)
    assert tasks[0]["title"] == "Ранняя"


@pytest.mark.asyncio
async def test_add_recurring_task(repo: TaskRepository):
    now = now_local()
    due_time = (now + timedelta(minutes=10)).strftime("%H:%M")

    task_id = await repo.add(
        USER_ID,
        "Выпить таблетки",
        "",
        now.strftime("%Y-%m-%d"),
        due_time,
        is_recurring=True,
    )

    tasks = await repo.get_active(USER_ID)
    assert len(tasks) == 1
    assert tasks[0]["id"] == task_id
    assert tasks[0]["is_recurring"] == 1


@pytest.mark.asyncio
async def test_get_due_soon_recurring(repo: TaskRepository):
    now = now_local()
    due_time = (now + timedelta(minutes=10)).strftime("%H:%M")
    await repo.add(USER_ID, "Выпить таблетки", "", now.strftime("%Y-%m-%d"), due_time, is_recurring=True)

    tasks = await repo.get_due_soon(within_minutes=30)
    assert any(task["due_time"] == due_time and task["is_recurring"] == 1 for task in tasks)
