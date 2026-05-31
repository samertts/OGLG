from __future__ import annotations

from pathlib import Path

from app.core.ui_recovery import UiRecoveryValidator


class TestPyQt6CrashReplay:
    def test_crash_replay(self, tmp_path: Path):
        v = UiRecoveryValidator(tmp_path)
        r = v.validate_pyqt6_crash_replay()
        assert r.passed, r.detail


class TestDialogRecoveryReplay:
    def test_dialog_recovery(self, tmp_path: Path):
        v = UiRecoveryValidator(tmp_path)
        r = v.validate_dialog_recovery_replay()
        assert r.passed, r.detail


class TestRenderInterruptionRecovery:
    def test_render_interrupt(self, tmp_path: Path):
        v = UiRecoveryValidator(tmp_path)
        r = v.validate_render_interruption_recovery()
        assert r.passed, r.detail


class TestOrphanWidgetCleanup:
    def test_orphan_cleanup(self, tmp_path: Path):
        v = UiRecoveryValidator(tmp_path)
        r = v.validate_orphan_widget_cleanup()
        assert r.passed, r.detail


class TestSignalLeakVerification:
    def test_signal_leak(self, tmp_path: Path):
        v = UiRecoveryValidator(tmp_path)
        r = v.validate_signal_leak_verification()
        assert r.passed, r.detail


class TestWindowLifecycleReplay:
    def test_window_lifecycle(self, tmp_path: Path):
        v = UiRecoveryValidator(tmp_path)
        r = v.validate_window_lifecycle_replay()
        assert r.passed, r.detail


class TestUiRollbackContinuity:
    def test_rollback(self, tmp_path: Path):
        v = UiRecoveryValidator(tmp_path)
        r = v.validate_ui_rollback_continuity()
        assert r.passed, r.detail


class TestLowMemoryUiReplay:
    def test_low_mem_ui(self, tmp_path: Path):
        v = UiRecoveryValidator(tmp_path)
        r = v.validate_low_memory_ui_replay()
        assert r.passed, r.detail


class TestSessionRestoration:
    def test_session(self, tmp_path: Path):
        v = UiRecoveryValidator(tmp_path)
        r = v.validate_session_restoration()
        assert r.passed, r.detail


class TestDeterministicUiRecovery:
    def test_det_ui(self, tmp_path: Path):
        v = UiRecoveryValidator(tmp_path)
        r = v.validate_deterministic_ui_recovery()
        assert r.passed, r.detail


class TestMonotonicClockReplay:
    def test_monotonic(self, tmp_path: Path):
        v = UiRecoveryValidator(tmp_path)
        r = v.validate_monotonic_clock_replay()
        assert r.passed, r.detail


class TestReplayTimestampNormalization:
    def test_timestamp_norm(self, tmp_path: Path):
        v = UiRecoveryValidator(tmp_path)
        r = v.validate_replay_timestamp_normalization()
        assert r.passed, r.detail


class TestTimezoneIsolation:
    def test_timezone(self, tmp_path: Path):
        v = UiRecoveryValidator(tmp_path)
        r = v.validate_timezone_isolation()
        assert r.passed, r.detail


class TestValidateAll:
    def test_all_ui_recovery(self, tmp_path: Path):
        v = UiRecoveryValidator(tmp_path)
        results = v.validate_all()
        assert len(results) == 13
        passed = sum(1 for r in results if r.passed)
        assert passed >= 12, f"passed={passed}/13: {[r.scenario for r in results if not r.passed]}"

    def test_each_has_duration(self, tmp_path: Path):
        v = UiRecoveryValidator(tmp_path)
        for r in v.validate_all():
            assert r.duration_seconds >= 0
