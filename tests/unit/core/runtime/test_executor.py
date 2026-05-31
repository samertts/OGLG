from __future__ import annotations

import asyncio

import pytest

from app.core.runtime.executor import AsyncTaskExecutor


@pytest.mark.asyncio
async def test_executor_start_stop() -> None:
    executor = AsyncTaskExecutor(max_workers=2)
    assert not executor.is_running
    executor.start()
    assert executor.is_running
    executor.stop()
    assert not executor.is_running


@pytest.mark.asyncio
async def test_executor_submit() -> None:
    executor = AsyncTaskExecutor(max_workers=2)
    executor.start()
    try:

        async def add(a: int, b: int) -> int:
            return a + b

        future = executor.submit(add(1, 2))
        result = future.result(timeout=5.0)
        assert result == 3
    finally:
        executor.stop()


@pytest.mark.asyncio
async def test_executor_submit_not_running() -> None:
    executor = AsyncTaskExecutor(max_workers=2)
    with pytest.raises(RuntimeError, match="not running"):
        executor.submit(asyncio.sleep(0))


@pytest.mark.asyncio
async def test_executor_state() -> None:
    executor = AsyncTaskExecutor(max_workers=4)
    executor.start()
    state = executor.state()
    assert state["running"] is True
    assert state["max_workers"] == 4
    executor.stop()
