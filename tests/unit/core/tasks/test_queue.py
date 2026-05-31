from __future__ import annotations

import pytest

from app.core.tasks.base import TaskPriority, TaskState
from app.core.tasks.queue import BackgroundJobQueue


@pytest.mark.asyncio
async def test_queue_enqueue_and_process() -> None:
    queue = BackgroundJobQueue()

    async def add(a: int, b: int) -> int:
        return a + b

    await queue.enqueue("task1", add(1, 2))
    assert queue.qsize == 1

    tid = await queue.process_next()
    assert tid == "task1"
    assert queue.get_result("task1") == 3
    assert queue.get_state("task1") == TaskState.COMPLETED


@pytest.mark.asyncio
async def test_queue_priority_order() -> None:
    queue = BackgroundJobQueue()

    async def make(value: int) -> int:
        return value

    await queue.enqueue("low", make(1), priority=TaskPriority.LOW)
    await queue.enqueue("critical", make(2), priority=TaskPriority.CRITICAL)
    await queue.enqueue("high", make(3), priority=TaskPriority.HIGH)
    await queue.enqueue("normal", make(4), priority=TaskPriority.NORMAL)

    tids = await queue.process_all(max_batch=4)
    assert tids[0] == "critical"
    assert tids[1] == "high"
    assert tids[2] == "normal"
    assert tids[3] == "low"


@pytest.mark.asyncio
async def test_queue_error_handling() -> None:
    queue = BackgroundJobQueue()

    async def fail() -> None:
        raise ValueError("boom")

    await queue.enqueue("fail", fail())
    tid = await queue.process_next()
    assert tid == "fail"
    assert queue.get_state("fail") == TaskState.FAILED
    assert isinstance(queue.get_error("fail"), ValueError)


@pytest.mark.asyncio
async def test_queue_clear_completed() -> None:
    queue = BackgroundJobQueue()

    async def ok() -> int:
        return 1

    await queue.enqueue("t1", ok())
    await queue.process_next()
    cleared = await queue.clear_completed()
    assert cleared == 1
    assert queue.get_result("t1") is None
    assert queue.get_state("t1") is None


@pytest.mark.asyncio
async def test_queue_state_summary() -> None:
    queue = BackgroundJobQueue()
    summary = queue.state_summary()
    assert summary["pending"] == 0
    assert summary["completed"] == 0
