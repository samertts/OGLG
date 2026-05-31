from __future__ import annotations

from pathlib import Path

from app.core.stress.archive_ingestion import ArchiveIngestionValidator


class TestLargeImport:
    def test_large_import(self, tmp_path: Path):
        v = ArchiveIngestionValidator(tmp_path)
        r = v.validate_large_import()
        assert r.passed, r.detail


class TestArabicIndexing:
    def test_arabic(self, tmp_path: Path):
        v = ArchiveIngestionValidator(tmp_path)
        r = v.validate_arabic_indexing()
        assert r.passed, r.detail


class TestAttachmentHeavyIngestion:
    def test_attachment_heavy(self, tmp_path: Path):
        v = ArchiveIngestionValidator(tmp_path)
        r = v.validate_attachment_heavy_ingestion()
        assert r.passed, r.detail


class TestArchiveReplay:
    def test_replay(self, tmp_path: Path):
        v = ArchiveIngestionValidator(tmp_path)
        r = v.validate_archive_replay()
        assert r.passed, r.detail


class TestCorruptedAttachmentIsolation:
    def test_corrupted_attachment(self, tmp_path: Path):
        v = ArchiveIngestionValidator(tmp_path)
        r = v.validate_corrupted_attachment_isolation()
        assert r.passed, r.detail


class TestDeterministicPagination:
    def test_pagination(self, tmp_path: Path):
        v = ArchiveIngestionValidator(tmp_path)
        r = v.validate_deterministic_pagination()
        assert r.passed, r.detail


class TestFts5Rebuild:
    def test_fts5(self, tmp_path: Path):
        v = ArchiveIngestionValidator(tmp_path)
        r = v.validate_fts5_rebuild()
        assert r.passed, r.detail


class TestLongSessionBrowsing:
    def test_long_session(self, tmp_path: Path):
        v = ArchiveIngestionValidator(tmp_path)
        r = v.validate_long_session_browsing()
        assert r.passed, r.detail


class TestCompactionContinuity:
    def test_compaction(self, tmp_path: Path):
        v = ArchiveIngestionValidator(tmp_path)
        r = v.validate_compaction_continuity()
        assert r.passed, r.detail


class TestValidateAll:
    def test_all_ingestion_scenarios(self, tmp_path: Path):
        v = ArchiveIngestionValidator(tmp_path)
        results = v.validate_all()
        assert len(results) == 9
        passed = sum(1 for r in results if r.passed)
        assert passed >= 8, f"passed={passed}/9: {[r.scenario for r in results if not r.passed]}"

    def test_each_has_duration(self, tmp_path: Path):
        v = ArchiveIngestionValidator(tmp_path)
        for r in v.validate_all():
            assert r.duration_seconds >= 0
