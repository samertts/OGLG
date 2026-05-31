from __future__ import annotations

from app.core.runtime.lazy import LazyLoader


def test_lazy_loader_loads_once() -> None:
    call_count = 0

    def factory() -> int:
        nonlocal call_count
        call_count += 1
        return 42

    loader = LazyLoader(factory)
    assert not loader.is_loaded
    assert loader.get() == 42
    assert loader.is_loaded
    assert loader.get() == 42
    assert call_count == 1


def test_lazy_loader_reset() -> None:
    call_count = 0

    def factory() -> int:
        nonlocal call_count
        call_count += 1
        return call_count

    loader = LazyLoader(factory)
    assert loader.get() == 1
    loader.reset()
    assert not loader.is_loaded
    assert loader.get() == 2


def test_lazy_loader_repr() -> None:
    def factory() -> int:
        return 0

    loader = LazyLoader(factory, name="test")
    assert "LazyLoader(test, pending)" in repr(loader)
    loader.get()
    assert "LazyLoader(test, loaded)" in repr(loader)
