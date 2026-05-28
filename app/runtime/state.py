"""Runtime state machine with strict transition enforcement.

Defines the application lifecycle states and controls valid transitions
between them. Prevents invalid state changes during startup, operation,
recovery, and shutdown.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any

from app.utils.logger import get_logger

logger = get_logger("app.runtime.state")


class RuntimeState(enum.Enum):
    """All possible runtime states of the application."""

    UNINITIALIZED = "UNINITIALIZED"
    INITIALIZING = "INITIALIZING"
    VALIDATING = "VALIDATING"
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    RECOVERING = "RECOVERING"
    SHUTTING_DOWN = "SHUTTING_DOWN"
    STOPPED = "STOPPED"
    FAILED = "FAILED"


_VALID_TRANSITIONS: dict[RuntimeState, set[RuntimeState]] = {
    RuntimeState.UNINITIALIZED: {RuntimeState.INITIALIZING, RuntimeState.FAILED},
    RuntimeState.INITIALIZING: {RuntimeState.VALIDATING, RuntimeState.FAILED},
    RuntimeState.VALIDATING: {RuntimeState.STARTING, RuntimeState.RECOVERING, RuntimeState.FAILED},
    RuntimeState.STARTING: {RuntimeState.RUNNING, RuntimeState.FAILED},
    RuntimeState.RUNNING: {RuntimeState.RECOVERING, RuntimeState.SHUTTING_DOWN, RuntimeState.FAILED},
    RuntimeState.RECOVERING: {RuntimeState.VALIDATING, RuntimeState.SHUTTING_DOWN, RuntimeState.FAILED},
    RuntimeState.SHUTTING_DOWN: {RuntimeState.STOPPED, RuntimeState.FAILED},
    RuntimeState.STOPPED: {RuntimeState.UNINITIALIZED},
    RuntimeState.FAILED: {RuntimeState.UNINITIALIZED, RuntimeState.RECOVERING},
}


class StateTransitionError(Exception):
    """Raised when an invalid state transition is attempted."""


@dataclass
class RuntimeStateMachine:
    """Strict runtime state machine with transition logging.

    Usage:
        machine = RuntimeStateMachine()
        machine.transition_to(RuntimeState.INITIALIZING)
        machine.transition_to(RuntimeState.VALIDATING)
        # ...
        machine.transition_to(RuntimeState.RUNNING)
    """

    current: RuntimeState = field(default=RuntimeState.UNINITIALIZED)
    previous: RuntimeState | None = field(default=None)
    _transition_count: int = field(default=0, repr=False)

    def transition_to(self, target: RuntimeState) -> None:
        """Transition to a new state, validating the transition.

        Args:
            target: The target RuntimeState.

        Raises:
            StateTransitionError: If the transition is not allowed.
        """
        allowed = _VALID_TRANSITIONS.get(self.current, set())
        if target not in allowed:
            raise StateTransitionError(
                f"Invalid transition: {self.current.value} -> {target.value}"
            )

        self.previous = self.current
        self.current = target
        self._transition_count += 1

        logger.info(
            "State transition",
            extra={
                "from": self.previous.value,
                "to": self.current.value,
                "count": self._transition_count,
            },
        )

    def is_in(self, *states: RuntimeState) -> bool:
        """Check if the machine is in one of the given states."""
        return self.current in states

    def has_passed_through(self, state: RuntimeState) -> bool:
        """Check if the machine has ever been in the given state."""
        return self._transition_count > 0 and (
            self.previous == state or self.current == state
        )

    @property
    def is_running(self) -> bool:
        return self.current == RuntimeState.RUNNING

    @property
    def is_failed(self) -> bool:
        return self.current == RuntimeState.FAILED

    @property
    def is_stopped(self) -> bool:
        return self.current == RuntimeState.STOPPED

    def reset(self) -> None:
        """Reset the machine to uninitialized state."""
        self.current = RuntimeState.UNINITIALIZED
        self.previous = None
        self._transition_count = 0
        logger.info("State machine reset")
