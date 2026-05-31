from __future__ import annotations

from app.core.queue.commands import (
    CommandEntry,
    CommandLifecycle,
    CommandPriority,
    CommandState,
)


def test_command_entry_defaults() -> None:
    cmd = CommandEntry(command_type="test", aggregate_id="agg-1")
    assert cmd.command_id is not None
    assert cmd.state == CommandState.PENDING
    assert cmd.priority == CommandPriority.NORMAL


def test_command_lifecycle_prepare() -> None:
    cmd = CommandEntry(command_type="test")
    lifecycle = CommandLifecycle(max_attempts=3)
    lifecycle.prepare(cmd)
    assert cmd.state == CommandState.QUEUED


def test_command_lifecycle_complete() -> None:
    cmd = CommandEntry(command_type="test")
    lifecycle = CommandLifecycle()
    lifecycle.prepare(cmd)
    lifecycle.mark_dispatched(cmd)
    lifecycle.mark_completed(cmd)
    assert cmd.state == CommandState.COMPLETED


def test_command_lifecycle_fail_and_retry() -> None:
    cmd = CommandEntry(command_type="test")
    lifecycle = CommandLifecycle(max_attempts=3)
    lifecycle.prepare(cmd)
    lifecycle.mark_dispatched(cmd)
    lifecycle.mark_failed(cmd, "error-1")
    assert cmd.state == CommandState.FAILED
    assert cmd.status.attempts == 1
    assert lifecycle.can_retry(cmd)
    lifecycle.prepare(cmd)
    lifecycle.mark_dispatched(cmd)
    lifecycle.mark_failed(cmd, "error-2")
    lifecycle.prepare(cmd)
    lifecycle.mark_dispatched(cmd)
    lifecycle.mark_failed(cmd, "error-3")
    assert cmd.state == CommandState.DEAD_LETTER
    assert not lifecycle.can_retry(cmd)
