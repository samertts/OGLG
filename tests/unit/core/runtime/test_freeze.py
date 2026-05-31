from __future__ import annotations

import time

from app.core.runtime.freeze import FreezeWatchdog


def test_freeze_no_heartbeat() -> None:
    watchdog = FreezeWatchdog(timeout=0.1, check_interval=0.05)
    detected: list[float] = []

    def on_freeze(elapsed: float) -> None:
        detected.append(elapsed)

    watchdog.on_freeze(on_freeze)
    watchdog.start()
    time.sleep(0.3)
    watchdog.stop()
    assert len(detected) >= 1
    assert detected[0] >= 0.1


def test_freeze_with_heartbeat() -> None:
    watchdog = FreezeWatchdog(timeout=0.2, check_interval=0.05)
    detected: list[float] = []

    def on_freeze(elapsed: float) -> None:
        detected.append(elapsed)

    watchdog.on_freeze(on_freeze)
    watchdog.start()
    for _ in range(5):
        watchdog.heartbeat()
        time.sleep(0.05)
    time.sleep(0.1)
    watchdog.stop()
    assert len(detected) == 0
    assert not watchdog.is_frozen


def test_freeze_state() -> None:
    watchdog = FreezeWatchdog(timeout=1.0, check_interval=0.5)
    watchdog.heartbeat()
    state = watchdog.state()
    assert state["timeout"] == 1.0
    assert state["frozen"] is False
    assert state["seconds_since_heartbeat"] >= 0
