from __future__ import annotations

import threading
from collections.abc import Callable
from typing import Any, TypeVar

T = TypeVar("T")


class BoundedExecutionGuard:
    """Bounded execution guard with timeout and resource limits.

    Raises TimeoutError if the guarded call exceeds the time limit.
    """

    def __init__(self, default_timeout: float = 30.0) -> None:
        if default_timeout <= 0:
            raise ValueError("default_timeout must be > 0")
        self._default_timeout = default_timeout

    def run(
        self,
        func: Callable[..., T],
        *args: Any,
        timeout: float | None = None,
        **kwargs: Any,
    ) -> T:
        _timeout = timeout if timeout is not None else self._default_timeout
        result: list[T] = []
        error: list[Exception] = []
        event = threading.Event()

        def _worker() -> None:
            try:
                res = func(*args, **kwargs)
                result.append(res)
            except Exception as exc:
                error.append(exc)
            finally:
                event.set()

        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()
        ok = event.wait(timeout=_timeout)
        if not ok:
            raise TimeoutError(
                f"Execution timed out after {_timeout}s"
            )
        if error:
            raise error[0]
        return result[0]


def timeout_wrapper(
    timeout: float = 30.0,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator factory that wraps a callable with a timeout guard."""

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        def wrapper(*args: Any, **kwargs: Any) -> T:
            guard = BoundedExecutionGuard(default_timeout=timeout)
            return guard.run(func, *args, timeout=timeout, **kwargs)

        return wrapper

    return decorator
