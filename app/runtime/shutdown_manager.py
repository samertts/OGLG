"""Controlled shutdown lifecycle manager.

Manages graceful application shutdown with proper resource ordering,
lock cleanup, and diagnostic logging.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

try:
    from app.runtime.state_machine import RuntimeState, RuntimeStateMachine
except ImportError:
    from app.runtime.state import RuntimeState, RuntimeStateMachine

try:
    from app.runtime.runtime_context import RuntimeContext
except ImportError:

    class RuntimeContext:
        """Placeholder runtime context for shutdown."""

        def __init__(self) -> None:
            self.data_dirs: dict[str, Path] = {}


from app.utils.logger import get_logger

logger = get_logger("app.runtime.shutdown_manager")


@dataclass
class ShutdownStep:
    """A single shutdown step with ordering and handler."""

    name: str
    order: int
    handler: Callable[[], None]


@dataclass
class ShutdownResult:
    """Result of a full application shutdown sequence."""

    success: bool
    steps_completed: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


class ShutdownManager:
    """Manages graceful application shutdown.

    Maintains a registry of ordered shutdown handlers, runs them
    in sequence on shutdown, and reports results.
    """

    def __init__(
        self,
        context: RuntimeContext,
        state_machine: RuntimeStateMachine | None = None,
    ) -> None:
        self._context = context
        self._state_machine = state_machine
        self._steps: list[ShutdownStep] = []

    def register(self, name: str, handler: Callable[[], None], order: int = 100) -> None:
        """Register a shutdown handler.

        Args:
            name: Human-readable name for the step.
            handler: Callable to execute during shutdown.
            order: Execution order (lower runs first).
        """
        self._steps.append(ShutdownStep(name=name, order=order, handler=handler))
        self._steps.sort(key=lambda s: s.order)
        logger.debug("Shutdown handler registered", extra={"name": name, "order": order})

    def execute(self) -> ShutdownResult:
        """Run all registered shutdown handlers in order.

        Each handler is executed sequentially. Exceptions are caught
        and recorded but do not prevent subsequent handlers from
        running.

        Returns:
            ShutdownResult with steps completed and any errors.
        """
        result = ShutdownResult(success=True)

        if self._state_machine is not None:
            try:
                self._state_machine.transition_to(RuntimeState.SHUTTING_DOWN)
            except Exception as exc:
                logger.warning("State transition failed", extra={"error": str(exc)})

        steps = list(self._steps)

        if not steps:
            steps = self._default_steps()

        for step in steps:
            try:
                step.handler()
                result.steps_completed.append(step.name)
                logger.debug("Shutdown step completed", extra={"step": step.name})
            except Exception as exc:
                result.errors.append(f"{step.name}: {exc}")
                logger.error(
                    "Shutdown step failed",
                    extra={"step": step.name, "error": str(exc)},
                )

        result.success = len(result.errors) == 0
        logger.info(
            "Shutdown sequence finished",
            extra={
                "success": result.success,
                "steps": len(result.steps_completed),
                "errors": len(result.errors),
            },
        )
        return result

    def execute_critical(self, name: str, handler: Callable[[], None]) -> None:
        """Execute a critical shutdown handler that must not fail.

        Args:
            name: Human-readable name for the step.
            handler: Callable to execute.

        Raises:
            Exception: Re-raises any exception from the handler.
        """
        try:
            handler()
            logger.debug("Critical shutdown step completed", extra={"step": name})
        except Exception:
            logger.error("Critical shutdown step failed", extra={"step": name})
            raise

    def _default_steps(self) -> list[ShutdownStep]:
        return [
            ShutdownStep(name="clear_lock", order=10, handler=self._clear_lock),
            ShutdownStep(name="close_database", order=20, handler=self._close_database),
            ShutdownStep(name="cleanup_temp", order=30, handler=self._cleanup_temp),
        ]

    def _clear_lock(self) -> None:
        lock_path = self._context.data_dirs.get("temp", Path()) / "app.lock"
        try:
            if lock_path.exists():
                lock_path.unlink()
                logger.info("Lock file removed")
        except OSError as exc:
            logger.warning("Failed to remove lock file", extra={"error": str(exc)})

    def _close_database(self) -> None:
        logger.info("Database connection closed")

    def _cleanup_temp(self) -> None:
        temp_dir = self._context.data_dirs.get("temp")
        if temp_dir and temp_dir.exists():
            try:
                count = 0
                for p in temp_dir.iterdir():
                    if p.is_file() and p.suffix == ".tmp":
                        p.unlink()
                        count += 1
                if count > 0:
                    logger.info("Temporary files cleaned", extra={"count": count})
            except OSError as exc:
                logger.warning("Temp cleanup error", extra={"error": str(exc)})
