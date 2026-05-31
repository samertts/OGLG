from __future__ import annotations

from pathlib import Path

from app.core.stress.usb_offline_federation import UsbOfflineValidator


class TestUsbExchange:
    def test_exchange(self, tmp_path: Path):
        v = UsbOfflineValidator(tmp_path)
        r = v.validate_usb_exchange()
        assert r.passed, r.detail


class TestDelayedReplay:
    def test_delayed(self, tmp_path: Path):
        v = UsbOfflineValidator(tmp_path)
        r = v.validate_delayed_replay()
        assert r.passed, r.detail


class TestDuplicateDetection:
    def test_duplicate(self, tmp_path: Path):
        v = UsbOfflineValidator(tmp_path)
        r = v.validate_duplicate_detection()
        assert r.passed, r.detail


class TestInterruptedReplay:
    def test_interrupted(self, tmp_path: Path):
        v = UsbOfflineValidator(tmp_path)
        r = v.validate_interrupted_replay()
        assert r.passed, r.detail


class TestLowBandwidthSync:
    def test_low_bandwidth(self, tmp_path: Path):
        v = UsbOfflineValidator(tmp_path)
        r = v.validate_low_bandwidth_sync()
        assert r.passed, r.detail


class TestQueueRecovery:
    def test_queue_recovery(self, tmp_path: Path):
        v = UsbOfflineValidator(tmp_path)
        r = v.validate_queue_recovery()
        assert r.passed, r.detail


class TestAuditContinuity:
    def test_audit(self, tmp_path: Path):
        v = UsbOfflineValidator(tmp_path)
        r = v.validate_audit_continuity()
        assert r.passed, r.detail


class TestOfflineNodeRecovery:
    def test_offline_recovery(self, tmp_path: Path):
        v = UsbOfflineValidator(tmp_path)
        r = v.validate_offline_node_recovery()
        assert r.passed, r.detail


class TestDeterministicConflictReplay:
    def test_conflict(self, tmp_path: Path):
        v = UsbOfflineValidator(tmp_path)
        r = v.validate_deterministic_conflict_replay()
        assert r.passed, r.detail


class TestBoundedRetry:
    def test_retry(self, tmp_path: Path):
        v = UsbOfflineValidator(tmp_path)
        r = v.validate_bounded_retry()
        assert r.passed, r.detail


class TestValidateAll:
    def test_all_usb_offline(self, tmp_path: Path):
        v = UsbOfflineValidator(tmp_path)
        results = v.validate_all()
        assert len(results) == 10
        passed = sum(1 for r in results if r.passed)
        assert passed >= 9, f"passed={passed}/10: {[r.scenario for r in results if not r.passed]}"

    def test_each_has_duration(self, tmp_path: Path):
        v = UsbOfflineValidator(tmp_path)
        for r in v.validate_all():
            assert r.duration_seconds >= 0
