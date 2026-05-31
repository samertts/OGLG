from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Callable


class WalState(Enum):
    HEALTHY = auto()
    CHECKPOINTING = auto()
    RECOVERING = auto()
    CORRUPTED = auto()
    UNKNOWN = auto()


class TransitionVerdict(Enum):
    ALLOWED = auto()
    BLOCKED = auto()
    DEFERRED = auto()


@dataclass
class ScreenTransition:
    from_screen: str
    to_screen: str
    timestamp: float = 0.0
    is_blocked: bool = False
    reason: str = ""


class WalSafeTransitionCoordinator:
    WAL_BLOCKED_SCREENS: tuple[str, ...] = (
        "backup", "diagnostics", "settings",
    )

    def __init__(self) -> None:
        self._wal_state: WalState = WalState.HEALTHY
        self._transitions: list[ScreenTransition] = []
        self._max_history: int = 50
        self._before_transition: Callable[[str, str], TransitionVerdict] | None = None
        self._cooldown_screens: dict[str, float] = {}

    @property
    def wal_state(self) -> WalState:
        return self._wal_state

    def set_wal_state(self, state: WalState) -> None:
        self._wal_state = state

    def set_before_transition(self, cb: Callable[[str, str], TransitionVerdict]) -> None:
        self._before_transition = cb

    def can_transition(self, from_screen: str, to_screen: str) -> TransitionVerdict:
        if self._wal_state in (WalState.CORRUPTED, WalState.UNKNOWN):
            return TransitionVerdict.BLOCKED

        if self._wal_state == WalState.RECOVERING:
            if to_screen in self.WAL_BLOCKED_SCREENS:
                return TransitionVerdict.BLOCKED
            return TransitionVerdict.DEFERRED

        if self._wal_state == WalState.CHECKPOINTING:
            if to_screen in self.WAL_BLOCKED_SCREENS:
                return TransitionVerdict.DEFERRED

        if self._before_transition:
            return self._before_transition(from_screen, to_screen)

        return TransitionVerdict.ALLOWED

    def record_transition(
        self, from_screen: str, to_screen: str,
        blocked: bool = False, reason: str = "",
    ) -> None:
        self._transitions.append(ScreenTransition(
            from_screen=from_screen, to_screen=to_screen,
            is_blocked=blocked, reason=reason,
        ))
        if len(self._transitions) > self._max_history:
            self._transitions.pop(0)

    def set_screen_cooldown(self, screen_id: str, seconds: float) -> None:
        self._cooldown_screens[screen_id] = seconds

    @property
    def transition_history(self) -> list[ScreenTransition]:
        return list(self._transitions)

    @property
    def blocked_count(self) -> int:
        return sum(1 for t in self._transitions if t.is_blocked)

    def reset(self) -> None:
        self._wal_state = WalState.HEALTHY
        self._transitions.clear()
