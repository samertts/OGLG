from __future__ import annotations

from app.core.chaos.endurance_monitor import EnduranceMonitor


class TestMemoryGrowthTracking:
    def test_memory_within_limits(self):
        monitor = EnduranceMonitor()
        report = monitor.check_memory_growth(100.0, 50.0)
        assert report.memory_mb_delta == 50.0
        assert not report.memory_exceeded
        assert report.passed

    def test_memory_exceeds_max(self):
        monitor = EnduranceMonitor()
        report = monitor.check_memory_growth(600.0, 50.0)
        assert report.memory_mb_delta == 550.0
        assert report.memory_exceeded
        assert not report.passed

    def test_memory_custom_max(self):
        monitor = EnduranceMonitor(max_memory_mb=100.0)
        report = monitor.check_memory_growth(200.0, 0.0)
        assert report.memory_exceeded

    def test_memory_no_growth(self):
        monitor = EnduranceMonitor()
        report = monitor.check_memory_growth(50.0, 50.0)
        assert report.memory_mb_delta == 0.0
        assert not report.memory_exceeded


class TestEventListenerLeak:
    def test_listeners_within_limits(self):
        monitor = EnduranceMonitor()
        report = monitor.check_event_listener_leak(100)
        assert not report.event_leak_detected
        assert report.passed

    def test_listeners_exceeded(self):
        monitor = EnduranceMonitor()
        report = monitor.check_event_listener_leak(600)
        assert report.event_leak_detected
        assert not report.passed


class TestOrphanTaskDetection:
    def test_no_orphans(self):
        monitor = EnduranceMonitor()
        report = monitor.check_orphan_tasks()
        assert report.orphan_task_count == 0
        assert not report.orphan_task_exceeded

    def test_orphans_exceeded(self):
        monitor = EnduranceMonitor()
        for i in range(150):
            monitor.record_orphan_task(f"task_{i}")
        report = monitor.check_orphan_tasks()
        assert report.orphan_task_exceeded

    def test_cleanup_clears_orphans(self):
        monitor = EnduranceMonitor()
        for i in range(10):
            monitor.record_orphan_task(f"task_{i}")
        assert monitor.check_orphan_tasks().orphan_task_count == 10
        monitor.cleanup()
        assert monitor.check_orphan_tasks().orphan_task_count == 0


class TestQueueGrowth:
    def test_queue_within_limits(self):
        monitor = EnduranceMonitor()
        report = monitor.check_queue_growth(500)
        assert not report.queue_exceeded

    def test_queue_exceeded(self):
        monitor = EnduranceMonitor()
        report = monitor.check_queue_growth(2000)
        assert report.queue_exceeded


class TestWalGrowth:
    def test_wal_within_limits(self):
        monitor = EnduranceMonitor()
        report = monitor.check_wal_growth(50.0)
        assert not report.wal_exceeded

    def test_wal_exceeded(self):
        monitor = EnduranceMonitor()
        report = monitor.check_wal_growth(500.0)
        assert report.wal_exceeded

    def test_reset_wal_space(self):
        monitor = EnduranceMonitor()
        monitor.reset_free_wal_space(100.0)
        report = monitor.check_wal_growth(50.0)
        assert report.wal_mb_growth == -50.0
        assert not report.wal_exceeded


class TestAsyncExhaustion:
    def test_async_within_limits(self):
        monitor = EnduranceMonitor()
        report = monitor.check_async_exhaustion(50)
        assert not report.async_exhausted

    def test_async_exhausted(self):
        monitor = EnduranceMonitor()
        report = monitor.check_async_exhaustion(500)
        assert report.async_exhausted
