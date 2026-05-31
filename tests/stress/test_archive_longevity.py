from __future__ import annotations

from pathlib import Path

from app.core.archive.longevity import LongevityValidator


class TestBoundedWALRetention:
    def test_wal_retention_bounded(self, tmp_path: Path):
        v = LongevityValidator(tmp_path)
        r = v.validate_bounded_wal_retention()
        assert r.passed, r.detail


class TestArchiveCompaction:
    def test_compaction_preserves_integrity(self, tmp_path: Path):
        v = LongevityValidator(tmp_path)
        r = v.validate_archive_compaction()
        assert r.passed, r.detail


class TestImmutableCheckpoints:
    def test_checkpoints_valid(self, tmp_path: Path):
        v = LongevityValidator(tmp_path)
        r = v.validate_immutable_checkpoints()
        assert r.passed, r.detail


class TestArchiveIntegrity:
    def test_integrity_detects_tampering(self, tmp_path: Path):
        v = LongevityValidator(tmp_path)
        r = v.validate_archive_integrity_verification()
        assert r.passed, r.detail


class TestCorruptionDrift:
    def test_drift_detected(self, tmp_path: Path):
        v = LongevityValidator(tmp_path)
        r = v.validate_corruption_drift_detection()
        assert r.passed, r.detail


class TestAttachmentDedup:
    def test_dedup(self, tmp_path: Path):
        v = LongevityValidator(tmp_path)
        r = v.validate_attachment_dedup()
        assert r.passed, r.detail


class TestBoundedCache:
    def test_cache_bounded(self, tmp_path: Path):
        v = LongevityValidator(tmp_path)
        r = v.validate_bounded_cache_persistence()
        assert r.passed, r.detail


class TestReplayContinuity:
    def test_replay_continuity(self, tmp_path: Path):
        v = LongevityValidator(tmp_path)
        r = v.validate_replay_continuity()
        assert r.passed, r.detail


class TestValidateAll:
    def test_all_longevity_scenarios(self, tmp_path: Path):
        v = LongevityValidator(tmp_path)
        results = v.validate_all()
        assert len(results) == 8
        passed = sum(1 for r in results if r.passed)
        assert passed >= 7, f"passed={passed}/8: {[r.scenario for r in results if not r.passed]}"

    def test_each_has_duration(self, tmp_path: Path):
        v = LongevityValidator(tmp_path)
        for r in v.validate_all():
            assert r.duration_seconds >= 0
