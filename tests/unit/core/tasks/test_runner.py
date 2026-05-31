from __future__ import annotations

import asyncio

import pytest

from app.core.tasks.runner import BoundedTaskRunner


@pytest.mark.asyncio
async def test_runner_basic_execution() -> None:
    runner = BoundedTaskRunner(max_concurrency=2, default_timeout=10.0)

    async def echo(value: int) -> int:
        return value

    result = await runner.run(echo(42))
    assert result == 42
    await runner.shutdown()


@pytest.mark.asyncio
async def test_runner_timeout() -> None:
    runner = BoundedTaskRunner(max_concurrency=1, default_timeout=0.1)

    async def slow() -> str:
        await asyncio.sleep(10.0)
        return "done"

    with pytest.raises(TimeoutError):
        await runner.run(slow())
    await runner.shutdown()


@pytest.mark.asyncio
async def test_runner_concurrency_limit() -> None:
    runner = BoundedTaskRunner(max_concurrency=2, default_timeout=10.0)

    async def track(value: int) -> int:
        return value

    tasks = [runner.run(track(i)) for i in range(5)]
    results = await asyncio.gather(*tasks)
    assert results == [0, 1, 2, 3, 4]
    assert runner.active_count == 0
    await runner.shutdown()


@pytest.mark.asyncio
async def test_runner_shutdown() -> None:
    runner = BoundedTaskRunner(max_concurrency=2, default_timeout=10.0)
    await runner.shutdown()
    assert runner.is_shutdown

    async def noop() -> None:
        pass

    with pytest.raises(RuntimeError, match="shut down"):
        await runner.run(noop())


@pytest.mark.asyncio
async def test_runner_state() -> None:
    runner = BoundedTaskRunner(max_concurrency=4, default_timeout=30.0)
    state = runner.state()
    assert state["max_concurrency"] == 4
    assert state["active_count"] == 0
    assert state["shutdown"] is False
    await runner.shutdown()
