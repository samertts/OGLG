from __future__ import annotations

import logging
import os
import tempfile
import threading
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class TempCleanupService:
    """Temp file cleanup framework with age-based eviction."""

    def __init__(
        self,
        temp_dir: str | Path | None = None,
        max_age_seconds: float = 3600.0,
        cleanup_interval: float = 300.0,
    ) -> None:
        self._temp_dir = Path(temp_dir) if temp_dir else Path(tempfile.gettempdir())
        self._max_age = max_age_seconds
        self._cleanup_interval = cleanup_interval
        self._prefixes: list[str] = []
        self._lock = threading.RLock()
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    @property
    def temp_dir(self) -> Path:
        return self._temp_dir

    def register_prefix(self, prefix: str) -> None:
        with self._lock:
            if prefix not in self._prefixes:
                self._prefixes.append(prefix)

    def unregister_prefix(self, prefix: str) -> None:
        with self._lock:
            self._prefixes[:] = [p for p in self._prefixes if p != prefix]

    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._cleanup_loop,
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=3.0)
            self._thread = None

    def _cleanup_loop(self) -> None:
        while not self._stop_event.is_set():
            self._do_cleanup()
            self._stop_event.wait(timeout=self._cleanup_interval)

    def _do_cleanup(self) -> int:
        removed = 0
        try:
            if not self._temp_dir.exists():
                return 0
            now = time.time()
            for entry in os.scandir(self._temp_dir):
                if self._stop_event.is_set():
                    break
                if entry.is_file() and self._matches_prefix(entry.name):
                    try:
                        age = now - entry.stat().st_mtime
                        if age >= self._max_age:
                            os.unlink(entry.path)
                            removed += 1
                    except OSError:
                        pass
        except PermissionError:
            pass
        return removed

    def _matches_prefix(self, name: str) -> bool:
        with self._lock:
            if not self._prefixes:
                return True
            return any(name.startswith(p) for p in self._prefixes)

    def cleanup_now(self) -> int:
        return self._do_cleanup()

    def state(self) -> dict[str, Any]:
        return {
            "temp_dir": str(self._temp_dir),
            "max_age_seconds": self._max_age,
            "cleanup_interval": self._cleanup_interval,
            "prefixes": list(self._prefixes),
            "running": self._thread is not None and self._thread.is_alive(),
        }
