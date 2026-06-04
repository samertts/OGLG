from __future__ import annotations

from pathlib import Path

from app.core.stress.operational_replay import OperationalReplayValidator


class TestLongSessionReplay:
    def test_session(self, tmp_path: Path):
        v = OperationalReplayValidator(tmp_path)
        r = v.validate_long_session_replay()
        assert r.passed, r.detail


class TestCrashRecoveryCycles:
    def test_crash(self, tmp_path: Path):
        v = OperationalReplayValidator(tmp_path)
        r = v.validate_crash_recovery_cycles()
        assert r.passed, r.detail


class TestWalInterruption:
    def test_wal_interrupt(self, tmp_path: Path):
        v = OperationalReplayValidator(tmp_path)
        r = v.validate_wal_interruption_replay()
        assert r.passed, r.detail


class TestQueuePersistence:
    def test_queue(self, tmp_path: Path):
        v = OperationalReplayValidator(tmp_path)
        r = v.validate_queue_persistence()
        assert r.passed, r.detail


class TestArchiveReplay:
    def test_archive(self, tmp_path: Path):
        v = OperationalReplayValidator(tmp_path)
        r = v.validate_archive_replay()
        assert r.passed, r.detail


class TestOperatorContention:
    def test_contention(self, tmp_path: Path):
        v = OperationalReplayValidator(tmp_path)
        r = v.validate_operator_contention()
        assert r.passed, r.detail


class TestDeterministicSync:
    def test_sync(self, tmp_path: Path):
        v = OperationalReplayValidator(tmp_path)
        r = v.validate_deterministic_sync()
        assert r.passed, r.detail


class TestLowMemoryEndurance:
    def test_low_memory(self, tmp_path: Path):
        v = OperationalReplayValidator(tmp_path)
        r = v.validate_low_memory_endurance()
        assert r.passed, r.detail


class TestAuditContinuity:
    def test_audit(self, tmp_path: Path):
        v = OperationalReplayValidator(tmp_path)
        r = v.validate_audit_continuity()
        assert r.passed, r.detail


class TestFinalConsistency:
    def test_consistency(self, tmp_path: Path):
        v = OperationalReplayValidator(tmp_path)
        r = v.validate_final_consistency()
        assert r.passed, r.detail


class TestValidateAll:
    def test_all_operational(self, tmp_path: Path):
        v = OperationalReplayValidator(tmp_path)
        results = v.validate_all()
        assert len(results) == 10
        passed = sum(1 for r in results if r.passed)
        assert passed >= 9, f"passed={passed}/10: {[r.scenario for r in results if not r.passed]}"

    def test_each_has_duration(self, tmp_path: Path):
        v = OperationalReplayValidator(tmp_path)
        for r in v.validate_all():
            assert r.duration_seconds >= 0
