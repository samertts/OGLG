from __future__ import annotations

from enum import Enum, auto


class ScreenLifecycleState(Enum):
    UNINITIALIZED = auto()
    INITIALIZING = auto()
    ACTIVE = auto()
    SUSPENDED = auto()
    STOPPED = auto()
    DISPOSED = auto()


class ScreenLifecycleManager:
    def __init__(self) -> None:
        self._states: dict[str, ScreenLifecycleState] = {}

    def get_state(self, screen_id: str) -> ScreenLifecycleState:
        return self._states.get(screen_id, ScreenLifecycleState.UNINITIALIZED)

    def mark_initializing(self, screen_id: str) -> None:
        self._states[screen_id] = ScreenLifecycleState.INITIALIZING

    def mark_active(self, screen_id: str) -> None:
        self._states[screen_id] = ScreenLifecycleState.ACTIVE

    def mark_suspended(self, screen_id: str) -> None:
        self._states[screen_id] = ScreenLifecycleState.SUSPENDED

    def mark_stopped(self, screen_id: str) -> None:
        self._states[screen_id] = ScreenLifecycleState.STOPPED

    def mark_disposed(self, screen_id: str) -> None:
        self._states[screen_id] = ScreenLifecycleState.DISPOSED

    def reset(self, screen_id: str) -> None:
        self._states.pop(screen_id, None)

    @property
    def active_screens(self) -> list[str]:
        return [sid for sid, state in self._states.items() if state == ScreenLifecycleState.ACTIVE]

    @property
    def suspended_screens(self) -> list[str]:
        return [
            sid for sid, state in self._states.items() if state == ScreenLifecycleState.SUSPENDED
        ]

    @property
    def total_screens(self) -> int:
        return len(self._states)
