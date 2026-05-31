from __future__ import annotations

from pathlib import Path

from app.core.stress.archive_scale import ArchiveScaleValidator


class TestMillionRecordSimulation:
    def test_million_record(self, tmp_path: Path):
        v = ArchiveScaleValidator(tmp_path)
        r = v.validate_million_record_simulation()
        assert r.passed, r.detail


class TestHeavyAttachmentIndexing:
    def test_heavy_attachments(self, tmp_path: Path):
        v = ArchiveScaleValidator(tmp_path)
        r = v.validate_heavy_attachment_indexing()
        assert r.passed, r.detail


class TestLargeFts5Replay:
    def test_large_fts5(self, tmp_path: Path):
        v = ArchiveScaleValidator(tmp_path)
        r = v.validate_large_fts5_replay()
        assert r.passed, r.detail


class TestPaginationEndurance:
    def test_pagination(self, tmp_path: Path):
        v = ArchiveScaleValidator(tmp_path)
        r = v.validate_pagination_endurance()
        assert r.passed, r.detail


class TestArchiveReplayReconstruction:
    def test_replay_reconstruction(self, tmp_path: Path):
        v = ArchiveScaleValidator(tmp_path)
        r = v.validate_archive_replay_reconstruction()
        assert r.passed, r.detail


class TestWalGrowthEndurance:
    def test_wal_growth(self, tmp_path: Path):
        v = ArchiveScaleValidator(tmp_path)
        r = v.validate_wal_growth_endurance()
        assert r.passed, r.detail


class TestLongSessionArchiveBrowsing:
    def test_browsing(self, tmp_path: Path):
        v = ArchiveScaleValidator(tmp_path)
        r = v.validate_long_session_archive_browsing()
        assert r.passed, r.detail


class TestAttachmentCorruptionIsolation:
    def test_corruption_isolation(self, tmp_path: Path):
        v = ArchiveScaleValidator(tmp_path)
        r = v.validate_attachment_corruption_isolation()
        assert r.passed, r.detail


class TestReplaySafeArchiveRecovery:
    def test_replay_safe_recovery(self, tmp_path: Path):
        v = ArchiveScaleValidator(tmp_path)
        r = v.validate_replay_safe_archive_recovery()
        assert r.passed, r.detail


class TestBoundedCachePersistence:
    def test_bounded_cache(self, tmp_path: Path):
        v = ArchiveScaleValidator(tmp_path)
        r = v.validate_bounded_cache_persistence()
        assert r.passed, r.detail


class TestValidateAll:
    def test_all_archive_scale(self, tmp_path: Path):
        v = ArchiveScaleValidator(tmp_path)
        results = v.validate_all()
        assert len(results) == 10
        passed = sum(1 for r in results if r.passed)
        assert passed >= 9, f"passed={passed}/10: {[r.scenario for r in results if not r.passed]}"

    def test_each_has_duration(self, tmp_path: Path):
        v = ArchiveScaleValidator(tmp_path)
        for r in v.validate_all():
            assert r.duration_seconds >= 0
