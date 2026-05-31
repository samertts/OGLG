from __future__ import annotations

from app.ui.runtime.cancellation import CancellationToken, SafeCancellation
from app.ui.runtime.runtime_monitor import MemoryPressureLevel, RuntimeMonitor
from app.ui.runtime.task_scheduler import TaskScheduler


class TestRuntimeMonitor:
    def test_initial_metrics(self):
        mon = RuntimeMonitor()
        assert mon.metrics.cpu_percent == 0.0

    def test_update_metrics(self):
        mon = RuntimeMonitor()
        mon.update(cpu=50.0, memory_mb=256.0)
        assert mon.metrics.cpu_percent == 50.0
        assert mon.metrics.memory_mb == 256.0

    def test_memory_pressure_none(self):
        mon = RuntimeMonitor(max_memory_mb=1024, max_widgets=500)
        mon.update(memory_mb=100.0, widget_count=50)
        assert mon.pressure_level == MemoryPressureLevel.NONE

    def test_memory_pressure_high(self):
        mon = RuntimeMonitor(max_memory_mb=1024, max_widgets=500)
        mon.update(memory_mb=800.0, widget_count=400)
        assert mon.pressure_level in (MemoryPressureLevel.HIGH, MemoryPressureLevel.CRITICAL)

    def test_memory_pressure_critical(self):
        mon = RuntimeMonitor(max_memory_mb=100, max_widgets=100)
        mon.update(memory_mb=95.0, widget_count=95)
        assert mon.pressure_level == MemoryPressureLevel.CRITICAL

    def test_in_pressure_flag(self):
        mon = RuntimeMonitor(max_memory_mb=100, max_widgets=100)
        mon.update(memory_mb=80.0, widget_count=80)
        assert mon.in_pressure

    def test_is_critical(self):
        mon = RuntimeMonitor(max_memory_mb=100, max_widgets=100)
        mon.update(memory_mb=95.0, widget_count=50)
        assert mon.is_critical

    def test_uptime_tracking(self):
        mon = RuntimeMonitor()
        assert mon.metrics.uptime_seconds >= 0

    def test_widget_count_tracking(self):
        mon = RuntimeMonitor()
        mon.update(widget_count=42)
        assert mon.metrics.widget_count == 42


class TestSafeCancellation:
    def test_create_token(self):
        sc = SafeCancellation()
        token = sc.create_token("op-1")
        assert not token.is_cancelled

    def test_cancel_token(self):
        sc = SafeCancellation()
        sc.create_token("op-1")
        sc.cancel("op-1", "User cancelled")
        assert sc.is_cancelled("op-1")

    def test_cancel_invokes_callbacks(self):
        sc = SafeCancellation()
        calls = []
        sc.create_token("op-1")
        sc.on_cancel("op-1", lambda: calls.append("cancelled"))
        sc.cancel("op-1")
        assert len(calls) == 1

    def test_cancel_all(self):
        sc = SafeCancellation()
        sc.create_token("op-1")
        sc.create_token("op-2")
        sc.cancel_all("Shutdown")
        assert sc.is_cancelled("op-1")
        assert sc.is_cancelled("op-2")

    def test_remove_token(self):
        sc = SafeCancellation()
        sc.create_token("op-1")
        sc.remove("op-1")
        assert not sc.is_cancelled("op-1")

    def test_clear_all(self):
        sc = SafeCancellation()
        sc.create_token("op-1")
        sc.clear()
        assert sc.active_count == 0

    def test_active_count(self):
        sc = SafeCancellation()
        sc.create_token("op-1")
        sc.create_token("op-2")
        assert sc.active_count == 2


class TestTaskScheduler:
    def test_register_mount(self):
        ts = TaskScheduler()
        mount = ts.register_mount("w1", lambda: "widget")
        assert mount.widget_id == "w1"
        assert not mount.mounted

    def test_mount_widget(self):
        ts = TaskScheduler()
        ts.register_mount("w1", lambda: "widget")
        result = ts.mount("w1")
        assert result == "widget"
        assert ts.is_mounted("w1")

    def test_mount_unregistered_raises(self):
        ts = TaskScheduler()
        try:
            ts.mount("nonexistent")
            assert False
        except KeyError:
            pass

    def test_mount_count(self):
        ts = TaskScheduler()
        ts.register_mount("w1", lambda: None)
        ts.register_mount("w2", lambda: None)
        assert ts.mount_count == 2

    def test_schedule_task(self):
        ts = TaskScheduler()
        calls = []
        ts.schedule("task-1", lambda: calls.append("done"))
        assert True  # no exception
