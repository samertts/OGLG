"""Runtime state machine with strict transition enforcement.

Defines the application lifecycle states and controls valid transitions
between them. Emits structured events for each transition.
"""

from __future__ import annotations

import enum
import time
from dataclasses import dataclass
from datetime import datetime

from app.utils.logger import get_logger

logger = get_logger("app.runtime.state_machine")


class RuntimeState(enum.Enum):
    """All possible runtime states of the application lifecycle."""

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
    RuntimeState.RUNNING: {
        RuntimeState.RECOVERING,
        RuntimeState.SHUTTING_DOWN,
        RuntimeState.FAILED,
    },
    RuntimeState.RECOVERING: {
        RuntimeState.VALIDATING,
        RuntimeState.SHUTTING_DOWN,
        RuntimeState.FAILED,
    },
    RuntimeState.SHUTTING_DOWN: {RuntimeState.STOPPED, RuntimeState.FAILED},
    RuntimeState.STOPPED: {RuntimeState.UNINITIALIZED},
    RuntimeState.FAILED: {RuntimeState.UNINITIALIZED, RuntimeState.RECOVERING},
}


class StateTransitionError(RuntimeError):
    """Raised when an invalid state transition is attempted."""


@dataclass(frozen=True)
class StateChangedEvent:
    """Immutable record of a single state transition.

    Attributes:
        from_state: The state the machine transitioned from.
        to_state: The state the machine transitioned to.
        timestamp: When the transition occurred.
        duration_ms: Time spent in the previous state in milliseconds.
    """

    from_state: RuntimeState
    to_state: RuntimeState
    timestamp: datetime
    duration_ms: float


class RuntimeStateMachine:
    """Strict runtime state machine with transition event tracking.

    Enforces valid transitions between RuntimeState values and maintains
    a complete history of all state changes with timing information.
    """

    def __init__(self) -> None:
        self._state: RuntimeState = RuntimeState.UNINITIALIZED
        self._events: list[StateChangedEvent] = []
        self._previous_state: RuntimeState | None = None
        self._last_transition_time: float | None = None

    @property
    def current(self) -> RuntimeState:
        """Return the current runtime state."""
        return self._state

    @property
    def is_running(self) -> bool:
        """True when the machine is in the RUNNING state."""
        return self._state == RuntimeState.RUNNING

    @property
    def events(self) -> list[StateChangedEvent]:
        """Return a copy of all recorded state transition events."""
        return list(self._events)

    def can_transition_to(self, target: RuntimeState) -> bool:
        """Check whether a transition to *target* is valid from the current state.

        Args:
            target: The target RuntimeState to check.

        Returns:
            True if the transition is allowed.
        """
        allowed = _VALID_TRANSITIONS.get(self._state, set())
        return target in allowed

    def transition_to(self, target: RuntimeState) -> None:
        """Transition to a new state, validating and recording the event.

        Args:
            target: The target RuntimeState.

        Raises:
            StateTransitionError: If the transition is not allowed.
        """
        if not self.can_transition_to(target):
            raise StateTransitionError(f"Invalid transition: {self._state.value} -> {target.value}")

        monotonic_now = time.monotonic()
        if self._last_transition_time is not None:
            duration_ms = (monotonic_now - self._last_transition_time) * 1000.0
        else:
            duration_ms = 0.0

        self._previous_state = self._state
        self._state = target
        self._last_transition_time = monotonic_now

        event = StateChangedEvent(
            from_state=self._previous_state,
            to_state=self._state,
            timestamp=datetime.now(),
            duration_ms=round(duration_ms, 2),
        )
        self._events.append(event)

        logger.info(
            "State transition",
            extra={
                "from": event.from_state.value,
                "to": event.to_state.value,
                "duration_ms": event.duration_ms,
            },
        )

    def reset(self) -> None:
        """Reset the machine to UNINITIALIZED and clear all events."""
        self._state = RuntimeState.UNINITIALIZED
        self._events.clear()
        self._previous_state = None
        self._last_transition_time = None
        logger.info("State machine reset")

    def summary(self) -> dict:
        """Return a summary of the current state and all recorded transitions.

        Returns:
            A dictionary containing the current / previous state, total
            transition count, and a serialisable list of all events.
        """
        return {
            "current_state": self._state.value,
            "previous_state": self._previous_state.value if self._previous_state else None,
            "total_transitions": len(self._events),
            "events": [
                {
                    "from": e.from_state.value,
                    "to": e.to_state.value,
                    "timestamp": e.timestamp.isoformat(),
                    "duration_ms": e.duration_ms,
                }
                for e in self._events
            ],
        }
