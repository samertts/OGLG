from __future__ import annotations

import logging
import traceback
from collections.abc import Callable
from typing import Any, TypeVar

T = TypeVar("T")

logger = logging.getLogger(__name__)


class CrashSafeWrapper:
    """Crash-safe operation wrapper with structured error boundaries."""

    def __init__(
        self,
        fallback: T | None = None,
        reraise: bool = False,
        log_crashes: bool = True,
    ) -> None:
        self._fallback = fallback
        self._reraise = reraise
        self._log_crashes = log_crashes

    def run(
        self,
        func: Callable[..., T],
        *args: Any,
        fallback: T | None = None,
        **kwargs: Any,
    ) -> T:
        try:
            return func(*args, **kwargs)
        except Exception:
            if self._log_crashes:
                logger.error(
                    "Crash-safe boundary caught:\n%s",
                    traceback.format_exc(),
                )
            if self._reraise:
                raise
            resolved = fallback if fallback is not None else self._fallback
            return resolved  # type: ignore[return-value]


def crash_safe(
    fallback: Any = None,
    reraise: bool = False,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator that wraps a function in a crash-safe boundary."""

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        wrapper = CrashSafeWrapper(
            fallback=fallback,
            reraise=reraise,
        )

        def inner(*args: Any, **kwargs: Any) -> T:
            return wrapper.run(func, *args, **kwargs)

        return inner

    return decorator


def transaction_wrapper(
    commit: Callable[[], None] | None = None,
    rollback: Callable[[], None] | None = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator factory that wraps a function in a crash-safe transaction."""

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        def wrapper(*args: Any, **kwargs: Any) -> T:
            try:
                result = func(*args, **kwargs)
                if commit is not None:
                    commit()
                return result
            except Exception:
                if rollback is not None:
                    try:
                        rollback()
                    except Exception:
                        logger.error("Rollback failed:\n%s", traceback.format_exc())
                raise

        return wrapper

    return decorator
