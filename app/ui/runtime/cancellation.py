from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable


@dataclass
class CancellationToken:
    cancelled: bool = False
    reason: str | None = None
    cancelled_at: datetime | None = None

    def cancel(self, reason: str = "Cancelled") -> None:
        if not self.cancelled:
            self.cancelled = True
            self.reason = reason
            self.cancelled_at = datetime.now(timezone.utc)

    @property
    def is_cancelled(self) -> bool:
        return self.cancelled


class SafeCancellation:
    def __init__(self):
        self._tokens: dict[str, CancellationToken] = {}
        self._callbacks: dict[str, list[Callable[[], None]]] = {}

    def create_token(self, operation_id: str) -> CancellationToken:
        token = CancellationToken()
        self._tokens[operation_id] = token
        return token

    def cancel(self, operation_id: str, reason: str = "Cancelled") -> None:
        token = self._tokens.get(operation_id)
        if token is None:
            return
        token.cancel(reason)
        for cb in self._callbacks.get(operation_id, []):
            try:
                cb()
            except Exception:
                pass

    def cancel_all(self, reason: str = "Shutdown") -> None:
        for op_id in list(self._tokens.keys()):
            self.cancel(op_id, reason)

    def on_cancel(self, operation_id: str, callback: Callable[[], None]) -> None:
        if operation_id not in self._callbacks:
            self._callbacks[operation_id] = []
        self._callbacks[operation_id].append(callback)

    def is_cancelled(self, operation_id: str) -> bool:
        token = self._tokens.get(operation_id)
        if token is None:
            return False
        return token.is_cancelled

    def remove(self, operation_id: str) -> None:
        self._tokens.pop(operation_id, None)
        self._callbacks.pop(operation_id, None)

    def clear(self) -> None:
        self.cancel_all()
        self._tokens.clear()
        self._callbacks.clear()

    @property
    def active_count(self) -> int:
        return len(self._tokens)

    @property
    def tokens(self) -> dict[str, CancellationToken]:
        return dict(self._tokens)
