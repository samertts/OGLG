from __future__ import annotations

from pathlib import Path

from app.core.backup.validator import BackupValidator


class TestHotBackup:
    def test_hot_backup_consistent(self, tmp_path: Path):
        v = BackupValidator(tmp_path)
        r = v.validate_hot_backup()
        assert r.passed, r.detail
        assert r.integrity_ok


class TestColdBackup:
    def test_cold_backup_consistent(self, tmp_path: Path):
        v = BackupValidator(tmp_path)
        r = v.validate_cold_backup()
        assert r.passed, r.detail
        assert r.integrity_ok


class TestWALConsistentRestore:
    def test_wal_consistent_restore(self, tmp_path: Path):
        v = BackupValidator(tmp_path)
        r = v.validate_wal_consistent_restore()
        assert r.passed, r.detail
        assert r.integrity_ok


class TestArchiveReplayRestoration:
    def test_archive_replay(self, tmp_path: Path):
        v = BackupValidator(tmp_path)
        r = v.validate_archive_replay_restoration()
        assert r.passed, r.detail
        assert r.integrity_ok


class TestCorruptionRecoveryReplay:
    def test_corruption_recovery(self, tmp_path: Path):
        v = BackupValidator(tmp_path)
        r = v.validate_corruption_recovery_replay()
        assert r.passed, r.detail
        assert r.integrity_ok


class TestDeterministicRestoreOrdering:
    def test_deterministic_ordering(self, tmp_path: Path):
        v = BackupValidator(tmp_path)
        r = v.validate_deterministic_restore_ordering()
        assert r.passed, r.detail


class TestOfflineRestoreBundle:
    def test_offline_bundle(self, tmp_path: Path):
        v = BackupValidator(tmp_path)
        r = v.validate_offline_restore_bundle()
        assert r.passed, r.detail
        assert r.integrity_ok


class TestRollbackSafeRestore:
    def test_rollback_safe(self, tmp_path: Path):
        v = BackupValidator(tmp_path)
        r = v.validate_rollback_safe_restore()
        assert r.passed, r.detail
        assert r.integrity_ok


class TestValidateAll:
    def test_all_backup_scenarios(self, tmp_path: Path):
        v = BackupValidator(tmp_path)
        results = v.validate_all()
        assert len(results) == 8
        passed = sum(1 for r in results if r.passed)
        assert passed >= 7, f"passed={passed}/8: {[r.scenario for r in results if not r.passed]}"

    def test_each_has_duration(self, tmp_path: Path):
        v = BackupValidator(tmp_path)
        for r in v.validate_all():
            assert r.duration_seconds >= 0
