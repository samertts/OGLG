from __future__ import annotations

import time

from app.core.runtime.metrics import RuntimeMetrics


def test_metrics_increment() -> None:
    m = RuntimeMetrics()
    m.increment("requests")
    m.increment("requests", 3)
    snap = m.snapshot()
    assert snap["counters"]["requests"] == 4


def test_metrics_gauge() -> None:
    m = RuntimeMetrics()
    m.gauge("temperature", 36.6)
    snap = m.snapshot()
    assert snap["gauges"]["temperature"] == 36.6


def test_metrics_timing() -> None:
    m = RuntimeMetrics()
    with m.time("operation"):
        time.sleep(0.01)
    snap = m.snapshot()
    t = snap["timings"]["operation"]
    assert t["count"] == 1
    assert t["min"] >= 0.01
    assert t["max"] >= 0.01


def test_metrics_uptime() -> None:
    m = RuntimeMetrics()
    assert m.uptime >= 0
    original = m.uptime
    time.sleep(0.01)
    assert m.uptime > original


def test_metrics_reset() -> None:
    m = RuntimeMetrics()
    m.increment("x", 10)
    m.reset()
    snap = m.snapshot()
    assert snap["counters"] == {}
