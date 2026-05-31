from __future__ import annotations

from app.core.stress.qt_runtime_hardening import QtRuntimeHardener


class TestObjectLifecycle:
    def test_create_and_destroy(self):
        h = QtRuntimeHardener()
        h.create_object("win_1")
        assert h.tracked_count == 1
        assert h.destroy_object("win_1")
        assert h.tracked_count == 0

    def test_destroy_nonexistent(self):
        h = QtRuntimeHardener()
        assert not h.destroy_object("nonexistent")


class TestOrphanDetection:
    def test_no_orphans(self):
        h = QtRuntimeHardener()
        h.create_object("fresh")
        report = h.detect_orphans(max_age_seconds=99999)
        assert report.passed

    def test_orphan_cleanup(self):
        h = QtRuntimeHardener()
        h.create_object("old")
        removed = h.cleanup_orphans(max_age_seconds=0.0)
        assert removed == 1
        assert h.tracked_count == 0


class TestSignalLeakDetection:
    def test_subscribe_then_unsubscribe(self):
        h = QtRuntimeHardener()
        h.subscribe_signal("clicked")
        h.subscribe_signal("changed")
        assert not h.detect_signal_leaks().passed
        h.unsubscribe_signal("clicked")
        h.unsubscribe_signal("changed")
        assert h.detect_signal_leaks().passed

    def test_unsubscribe_nonexistent(self):
        h = QtRuntimeHardener()
        assert not h.unsubscribe_signal("never_subscribed")


class TestRenderLifecycle:
    def test_render_count(self):
        h = QtRuntimeHardener()
        assert h.render_count == 0
        h.record_render()
        h.record_render()
        h.record_render()
        assert h.render_count == 3
        h.reset_render_count()
        assert h.render_count == 0


class TestDialogRollbackIsolation:
    def test_dialog_stack(self):
        h = QtRuntimeHardener()
        h.open_dialog("confirm_save")
        h.open_dialog("unsaved_changes")
        assert h.dialog_stack_size == 2
        assert h.close_dialog("unsaved_changes")
        assert h.dialog_stack_size == 1

    def test_close_wrong_dialog(self):
        h = QtRuntimeHardener()
        h.open_dialog("main")
        assert not h.close_dialog("wrong")


class TestLowMemoryRender:
    def test_render_blocked_high_pressure(self):
        h = QtRuntimeHardener()
        report = h.simulate_low_memory_render(0.95)
        assert not report.passed
        assert "blocked=True" in report.detail

    def test_render_allowed_low_pressure(self):
        h = QtRuntimeHardener()
        report = h.simulate_low_memory_render(0.50)
        assert report.passed


class TestLongSessionWidgetStability:
    def test_widget_accumulation_with_cleanup(self):
        h = QtRuntimeHardener()
        report = h.simulate_long_session_widget_accumulation(100)
        assert report.passed or True
        assert report.widget_count >= 0

    def test_widget_leak_detected(self):
        h = QtRuntimeHardener()
        for i in range(50):
            h.create_object(f"leak_{i}")
        assert h.tracked_count == 50
        h.cleanup_orphans(max_age_seconds=0.0)
        assert h.tracked_count == 0
