from __future__ import annotations

from pathlib import Path

from app.core.stress.survivability import SurvivabilityValidator


class TestCrashRecoveryCycles:
    def test_crash_cycles(self, tmp_path: Path):
        v = SurvivabilityValidator(tmp_path)
        r = v.validate_crash_recovery_cycles()
        assert r.passed, r.detail


class TestDeterministicQueueReplay:
    def test_queue_replay(self, tmp_path: Path):
        v = SurvivabilityValidator(tmp_path)
        r = v.validate_deterministic_queue_replay()
        assert r.passed, r.detail


class TestWALInterruptionReplay:
    def test_wal_interruption(self, tmp_path: Path):
        v = SurvivabilityValidator(tmp_path)
        r = v.validate_wal_interruption_replay()
        assert r.passed, r.detail


class TestCorruptionSurvival:
    def test_corruption(self, tmp_path: Path):
        v = SurvivabilityValidator(tmp_path)
        r = v.validate_corruption_survival()
        assert r.passed, r.detail


class TestLowMemoryRuntime:
    def test_low_memory(self, tmp_path: Path):
        v = SurvivabilityValidator(tmp_path)
        r = v.validate_low_memory_runtime()
        assert r.passed, r.detail


class TestLongSessionEndurance:
    def test_endurance(self, tmp_path: Path):
        v = SurvivabilityValidator(tmp_path)
        r = v.validate_long_session_endurance()
        assert r.passed, r.detail


class TestConcurrentOperatorReplay:
    def test_concurrent_replay(self, tmp_path: Path):
        v = SurvivabilityValidator(tmp_path)
        r = v.validate_concurrent_operator_replay()
        assert r.passed, r.detail


class TestArchiveReplay:
    def test_archive_replay(self, tmp_path: Path):
        v = SurvivabilityValidator(tmp_path)
        r = v.validate_archive_replay()
        assert r.passed, r.detail


class TestDeterministicConsistency:
    def test_consistency(self, tmp_path: Path):
        v = SurvivabilityValidator(tmp_path)
        r = v.validate_deterministic_consistency()
        assert r.passed, r.detail


class TestValidateAll:
    def test_all_survivability_scenarios(self, tmp_path: Path):
        v = SurvivabilityValidator(tmp_path)
        results = v.validate_all()
        assert len(results) == 9
        passed = sum(1 for r in results if r.passed)
        assert passed >= 8, f"passed={passed}/9: {[r.scenario for r in results if not r.passed]}"

    def test_each_has_duration(self, tmp_path: Path):
        v = SurvivabilityValidator(tmp_path)
        for r in v.validate_all():
            assert r.duration_seconds >= 0
