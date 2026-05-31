from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum, auto


class LifecyclePhase(Enum):
    UNINITIALIZED = auto()
    INITIALIZING = auto()
    ACTIVE = auto()
    SUSPENDED = auto()
    STOPPED = auto()
    DISPOSED = auto()


@dataclass
class LifecycleState:
    phase: LifecyclePhase = LifecyclePhase.UNINITIALIZED
    activated_at: datetime | None = None
    suspended_at: datetime | None = None
    activation_count: int = 0
    suspend_count: int = 0
    error: str | None = None


class BoundedLifecycle:
    def __init__(self, widget_id: str, max_activations: int = 1000):
        self._widget_id = widget_id
        self._state = LifecycleState()
        self._max_activations = max_activations

    @property
    def widget_id(self) -> str:
        return self._widget_id

    @property
    def phase(self) -> LifecyclePhase:
        return self._state.phase

    def initialize(self) -> None:
        if self._state.phase != LifecyclePhase.UNINITIALIZED:
            return
        self._state.phase = LifecyclePhase.INITIALIZING

    def activate(self) -> None:
        if self._state.activation_count >= self._max_activations:
            msg = f"Max activations ({self._max_activations}) reached"
            raise RuntimeError(msg)
        if self._state.phase == LifecyclePhase.DISPOSED:
            raise RuntimeError(f"Cannot activate disposed widget: {self._widget_id}")
        self._state.phase = LifecyclePhase.ACTIVE
        self._state.activated_at = datetime.now(timezone.utc)
        self._state.activation_count += 1

    def suspend(self) -> None:
        if self._state.phase != LifecyclePhase.ACTIVE:
            return
        self._state.phase = LifecyclePhase.SUSPENDED
        self._state.suspended_at = datetime.now(timezone.utc)
        self._state.suspend_count += 1

    def stop(self) -> None:
        if self._state.phase == LifecyclePhase.DISPOSED:
            return
        self._state.phase = LifecyclePhase.STOPPED

    def dispose(self) -> None:
        self._state.phase = LifecyclePhase.DISPOSED

    def set_error(self, error: str) -> None:
        self._state.error = error

    @property
    def is_active(self) -> bool:
        return self._state.phase == LifecyclePhase.ACTIVE

    @property
    def is_disposed(self) -> bool:
        return self._state.phase == LifecyclePhase.DISPOSED

    @property
    def state(self) -> LifecycleState:
        return self._state
