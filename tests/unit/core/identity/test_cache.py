from __future__ import annotations

import time

from app.core.identity.cache import IdentityCache
from app.core.identity.models import UserIdentity


def test_cache_set_and_get() -> None:
    cache = IdentityCache(max_entries=10, ttl_seconds=60.0)
    user = UserIdentity(username="test")
    cache.set(user)
    cached = cache.get(user.user_id)
    assert cached is not None
    assert cached.username == "test"


def test_cache_miss() -> None:
    cache = IdentityCache(max_entries=10, ttl_seconds=60.0)
    result = cache.get("nonexistent")
    assert result is None


def test_cache_invalidate() -> None:
    cache = IdentityCache(max_entries=10, ttl_seconds=60.0)
    user = UserIdentity(username="test")
    cache.set(user)
    assert cache.invalidate(user.user_id) is True
    assert cache.get(user.user_id) is None


def test_cache_ttl_expiry() -> None:
    cache = IdentityCache(max_entries=10, ttl_seconds=0.1)
    user = UserIdentity(username="test")
    cache.set(user)
    time.sleep(0.2)
    assert cache.get(user.user_id) is None


def test_cache_eviction() -> None:
    cache = IdentityCache(max_entries=2, ttl_seconds=60.0)
    u1 = UserIdentity(username="a")
    u2 = UserIdentity(username="b")
    u3 = UserIdentity(username="c")
    cache.set(u1)
    cache.set(u2)
    cache.set(u3)
    assert cache.size <= 2


def test_cache_state() -> None:
    cache = IdentityCache(max_entries=100, ttl_seconds=300.0)
    state = cache.state()
    assert state["max_entries"] == 100
    assert state["ttl_seconds"] == 300.0
    assert state["size"] == 0
