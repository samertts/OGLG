from __future__ import annotations

import threading
import time
from typing import Any

from app.core.identity.models import UserId, UserIdentity


class IdentityCache:
    """Low-memory bounded identity cache with TTL eviction."""

    def __init__(
        self,
        max_entries: int = 500,
        ttl_seconds: float = 300.0,
    ) -> None:
        if max_entries < 1:
            raise ValueError("max_entries must be >= 1")
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be > 0")
        self._max = max_entries
        self._ttl = ttl_seconds
        self._cache: dict[UserId, tuple[UserIdentity, float]] = {}
        self._lock = threading.RLock()

    def get(self, user_id: UserId) -> UserIdentity | None:
        with self._lock:
            entry = self._cache.get(user_id)
            if entry is None:
                return None
            identity, expires = entry
            if time.monotonic() > expires:
                del self._cache[user_id]
                return None
            return identity

    def set(self, identity: UserIdentity) -> None:
        with self._lock:
            if len(self._cache) >= self._max:
                self._evict_one()
            expires = time.monotonic() + self._ttl
            self._cache[identity.user_id] = (identity, expires)

    def invalidate(self, user_id: UserId) -> bool:
        with self._lock:
            return self._cache.pop(user_id, None) is not None

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()

    def _evict_one(self) -> None:
        oldest: tuple[UserId, float] | None = None
        for uid, (_, expires) in self._cache.items():
            if oldest is None or expires < oldest[1]:
                oldest = (uid, expires)
        if oldest is not None:
            del self._cache[oldest[0]]

    @property
    def size(self) -> int:
        return len(self._cache)

    def state(self) -> dict[str, Any]:
        with self._lock:
            return {
                "max_entries": self._max,
                "ttl_seconds": self._ttl,
                "size": self.size,
            }
