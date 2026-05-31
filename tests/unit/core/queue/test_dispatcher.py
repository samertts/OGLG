from __future__ import annotations

import threading

from app.core.queue.commands import CommandEntry, CommandState
from app.core.queue.dispatcher import CommandDispatcher


def test_dispatcher_enqueue() -> None:
    d = CommandDispatcher(max_concurrency=2)
    cmd = d.enqueue_command("test", "agg-1", {"key": "val"})
    assert cmd.state == CommandState.QUEUED
    assert d.queue_size == 1


def test_dispatcher_dispatch_success() -> None:
    d = CommandDispatcher(max_concurrency=2)
    results: list[str] = []

    def handler(cmd: CommandEntry) -> None:
        results.append(cmd.command_id)

    d.register_handler("test", handler)
    d.enqueue_command("test", "agg-1")
    d.dispatch_next(timeout=5.0)
    assert len(results) == 1


def test_dispatcher_no_handler() -> None:
    d = CommandDispatcher(max_concurrency=2)
    d.enqueue_command("orphan", "agg-1")
    d.dispatch_next(timeout=5.0)
    assert d.dead_letter_size == 1


def test_dispatcher_concurrency_limit() -> None:
    d = CommandDispatcher(max_concurrency=1)
    release = threading.Event()
    started = threading.Event()

    def slow_handler(cmd: CommandEntry) -> None:
        started.set()
        release.wait(timeout=10.0)

    def fast_handler(cmd: CommandEntry) -> None:
        pass

    d.register_handler("slow", slow_handler)
    d.register_handler("fast", fast_handler)
    d.enqueue_command("slow", "agg-1")
    d.enqueue_command("fast", "agg-2")

    thread_result: list[CommandEntry | None] = [None]

    def _dispatch() -> None:
        thread_result[0] = d.dispatch_next(timeout=10.0)

    t = threading.Thread(target=_dispatch, daemon=True)
    t.start()
    started.wait(timeout=5.0)

    second = d.dispatch_next(timeout=0.5)
    assert second is None

    release.set()
    t.join(timeout=5.0)


def test_dispatcher_state() -> None:
    d = CommandDispatcher(max_concurrency=4, max_attempts=3)

    def handler(cmd: CommandEntry) -> None:
        pass

    d.register_handler("test", handler)
    d.enqueue_command("test")
    state = d.state()
    assert state["max_concurrency"] == 4
    assert state["queue_size"] == 1
    assert state["handlers"] == ["test"]
