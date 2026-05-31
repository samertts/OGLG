from __future__ import annotations

from pathlib import Path

from app.core.operational_closure import OperationalClosureValidator


class Test30DayReplayContinuity:
    def test_30_day(self, tmp_path: Path):
        v = OperationalClosureValidator(tmp_path)
        r = v.validate_30_day_replay_continuity()
        assert r.passed, r.detail


class TestStorageExhaustionReplay:
    def test_storage_exhaust(self, tmp_path: Path):
        v = OperationalClosureValidator(tmp_path)
        r = v.validate_storage_exhaustion_replay()
        assert r.passed, r.detail


class TestBoundedCacheEviction:
    def test_cache_eviction(self, tmp_path: Path):
        v = OperationalClosureValidator(tmp_path)
        r = v.validate_bounded_cache_eviction()
        assert r.passed, r.detail


class TestOrphanResourceCleanup:
    def test_orphan_cleanup(self, tmp_path: Path):
        v = OperationalClosureValidator(tmp_path)
        r = v.validate_orphan_resource_cleanup()
        assert r.passed, r.detail


class TestTimestampMonotonicity:
    def test_timestamp_mono(self, tmp_path: Path):
        v = OperationalClosureValidator(tmp_path)
        r = v.validate_timestamp_monotonicity()
        assert r.passed, r.detail


class TestArchiveDeterminism:
    def test_archive_det(self, tmp_path: Path):
        v = OperationalClosureValidator(tmp_path)
        r = v.validate_archive_determinism()
        assert r.passed, r.detail


class TestCrossSubsystemReplay:
    def test_cross_subsystem(self, tmp_path: Path):
        v = OperationalClosureValidator(tmp_path)
        r = v.validate_cross_subsystem_replay()
        assert r.passed, r.detail


class TestDeploymentRollbackContinuity:
    def test_rollback_cont(self, tmp_path: Path):
        v = OperationalClosureValidator(tmp_path)
        r = v.validate_deployment_rollback_continuity()
        assert r.passed, r.detail


class TestWalGrowthBounded:
    def test_wal_growth(self, tmp_path: Path):
        v = OperationalClosureValidator(tmp_path)
        r = v.validate_wal_growth_bounded()
        assert r.passed, r.detail


class TestMemoryBoundedRuntime:
    def test_memory_bounded(self, tmp_path: Path):
        v = OperationalClosureValidator(tmp_path)
        r = v.validate_memory_bounded_runtime()
        assert r.passed, r.detail


class TestConcurrentCrashRecovery:
    def test_crash_recovery(self, tmp_path: Path):
        v = OperationalClosureValidator(tmp_path)
        r = v.validate_concurrent_crash_recovery()
        assert r.passed, r.detail


class TestFinalDeterministicConsistency:
    def test_final_det(self, tmp_path: Path):
        v = OperationalClosureValidator(tmp_path)
        r = v.validate_final_deterministic_consistency()
        assert r.passed, r.detail


class TestValidateAll:
    def test_all_closure(self, tmp_path: Path):
        v = OperationalClosureValidator(tmp_path)
        results = v.validate_all()
        assert len(results) == 12
        passed = sum(1 for r in results if r.passed)
        assert passed >= 11, f"passed={passed}/12: {[r.scenario for r in results if not r.passed]}"

    def test_each_has_duration(self, tmp_path: Path):
        v = OperationalClosureValidator(tmp_path)
        for r in v.validate_all():
            assert r.duration_seconds >= 0
