"""Startup lifecycle logging and event tracking.

Records structured lifecycle events with timestamps and durations
for diagnostics and audit trails.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app.utils.logger import get_logger

logger = get_logger("app.runtime.lifecycle")


@dataclass
class LifecycleEvent:
    """A single lifecycle event with timing information."""

    step: str
    status: str
    timestamp: datetime = field(default_factory=datetime.now)
    duration_ms: float = 0.0
    detail: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "step": self.step,
            "status": self.status,
            "timestamp": self.timestamp.isoformat(),
            "duration_ms": round(self.duration_ms, 1),
            "detail": self.detail,
        }


class LifecycleLogger:
    """Tracks and logs application startup lifecycle events.

    Records each startup step with timing information and final
    summary of all steps.
    """

    def __init__(self) -> None:
        self._events: list[LifecycleEvent] = []
        self._step_start: datetime | None = None

    def begin_step(self, step: str) -> None:
        """Mark the beginning of a lifecycle step.

        Args:
            step: Name of the step (e.g. "config_loading").
        """
        self._step_start = datetime.now()
        logger.debug("Lifecycle step begin", extra={"step": step})

    def end_step(self, step: str, status: str = "ok", detail: str = "") -> None:
        """Mark the end of a lifecycle step with status.

        Args:
            step: Name of the step.
            status: "ok", "warning", or "error".
            detail: Optional detail message.
        """
        now = datetime.now()
        duration_ms = 0.0
        if self._step_start:
            duration_ms = (now - self._step_start).total_seconds() * 1000

        event = LifecycleEvent(
            step=step,
            status=status,
            timestamp=now,
            duration_ms=duration_ms,
            detail=detail,
        )
        self._events.append(event)

        log_fn = (
            logger.info
            if status == "ok"
            else logger.warning
            if status == "warning"
            else logger.error
        )
        log_fn(
            "Lifecycle step end",
            extra={
                "step": step,
                "status": status,
                "duration_ms": round(duration_ms, 1),
                "detail": detail,
            },
        )

    def record_event(self, step: str, status: str = "ok", detail: str = "") -> None:
        """Record a lifecycle event with automatic timing.

        Uses begin_step/end_step internally. Call once for each step.

        Args:
            step: Name of the step.
            status: "ok", "warning", or "error".
            detail: Optional detail message.
        """
        self.begin_step(step)
        self.end_step(step, status, detail)

    @property
    def events(self) -> list[LifecycleEvent]:
        return list(self._events)

    @property
    def total_duration_ms(self) -> float:
        if not self._events:
            return 0.0
        first = self._events[0].timestamp
        last = self._events[-1].timestamp
        return (last - first).total_seconds() * 1000

    @property
    def failed_steps(self) -> list[LifecycleEvent]:
        return [e for e in self._events if e.status == "error"]

    @property
    def warning_steps(self) -> list[LifecycleEvent]:
        return [e for e in self._events if e.status == "warning"]

    def summary(self) -> dict[str, Any]:
        """Generate a summary of all lifecycle events."""
        return {
            "total_steps": len(self._events),
            "failed": len(self.failed_steps),
            "warnings": len(self.warning_steps),
            "total_duration_ms": round(self.total_duration_ms, 1),
            "events": [e.to_dict() for e in self._events],
        }

    def print_summary(self) -> None:
        """Print a human-readable summary of the lifecycle."""
        total = self.total_duration_ms
        failed = self.failed_steps
        warnings = self.warning_steps

        logger.info(
            "Lifecycle complete",
            extra={
                "steps": len(self._events),
                "failed": len(failed),
                "warnings": len(warnings),
                "duration_ms": round(total, 1),
            },
        )

        if warnings:
            for w in warnings:
                logger.warning(
                    "Lifecycle warning",
                    extra={"step": w.step, "detail": w.detail},
                )

        if failed:
            for f in failed:
                logger.error(
                    "Lifecycle failure",
                    extra={"step": f.step, "detail": f.detail},
                )
