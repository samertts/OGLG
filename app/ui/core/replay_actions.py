from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable


@dataclass
class ReplayAction:
    action_id: str
    action_type: str
    payload: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    replay_token: str | None = None
    result: Any = None
    error: str | None = None


class ReplayActionLog:
    def __init__(self, max_entries: int = 1000):
        self._entries: list[ReplayAction] = []
        self._max_entries = max_entries

    def append(self, action: ReplayAction) -> None:
        self._entries.append(action)
        if len(self._entries) > self._max_entries:
            self._entries.pop(0)

    @property
    def entries(self) -> list[ReplayAction]:
        return list(self._entries)

    @property
    def count(self) -> int:
        return len(self._entries)

    def clear(self) -> None:
        self._entries.clear()

    def last(self, n: int = 10) -> list[ReplayAction]:
        return self._entries[-n:]


class ReplaySafeDispatcher:
    def __init__(self, log: ReplayActionLog | None = None):
        self._log = log or ReplayActionLog()
        self._handlers: dict[str, Callable[[ReplayAction], Any]] = {}

    def register(self, action_type: str, handler: Callable[[ReplayAction], Any]) -> None:
        self._handlers[action_type] = handler

    def dispatch(self, action: ReplayAction) -> Any:
        self._log.append(action)
        handler = self._handlers.get(action.action_type)
        if handler is None:
            action.error = f"No handler for action type: {action.action_type}"
            return None
        try:
            result = handler(action)
            action.result = result
            return result
        except Exception as e:
            action.error = str(e)
            return None

    def replay(self, action: ReplayAction) -> Any:
        action.replay_token = f"replay_{action.action_id}"
        return self.dispatch(action)
