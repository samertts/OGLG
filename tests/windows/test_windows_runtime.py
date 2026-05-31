from __future__ import annotations

from pathlib import Path

from app.platform.windows.runtime import WindowsRealityValidator


class TestNtfsWalBehavior:
    def test_wal_behavior(self, tmp_path: Path):
        v = WindowsRealityValidator(tmp_path)
        r = v.validate_ntfs_wal_behavior()
        assert r.passed, r.detail


class TestFileLockRecovery:
    def test_lock_recovery(self, tmp_path: Path):
        v = WindowsRealityValidator(tmp_path)
        r = v.validate_file_lock_recovery()
        assert r.passed, r.detail


class TestPortableDeployment:
    def test_portable(self, tmp_path: Path):
        v = WindowsRealityValidator(tmp_path)
        r = v.validate_portable_deployment()
        assert r.passed, r.detail


class TestPathNormalization:
    def test_path_norm(self, tmp_path: Path):
        v = WindowsRealityValidator(tmp_path)
        r = v.validate_path_normalization()
        assert r.passed, r.detail


class TestPrinterSubsystem:
    def test_printer(self, tmp_path: Path):
        v = WindowsRealityValidator(tmp_path)
        r = v.validate_printer_subsystem()
        assert r.passed, r.detail


class TestUnicodeArabicFs:
    def test_arabic(self, tmp_path: Path):
        v = WindowsRealityValidator(tmp_path)
        r = v.validate_unicode_arabic_fs()
        assert r.passed, r.detail


class TestSafeModeStartup:
    def test_safe_mode(self, tmp_path: Path):
        v = WindowsRealityValidator(tmp_path)
        r = v.validate_safe_mode_startup()
        assert r.passed, r.detail


class TestLowRamWindows:
    def test_low_ram(self, tmp_path: Path):
        v = WindowsRealityValidator(tmp_path)
        r = v.validate_low_ram_windows()
        assert r.passed, r.detail


class TestInterruptedShutdownReplay:
    def test_interrupted_shutdown(self, tmp_path: Path):
        v = WindowsRealityValidator(tmp_path)
        r = v.validate_interrupted_shutdown_replay()
        assert r.passed, r.detail


class TestPyQt6Lifecycle:
    def test_pyqt6_lifecycle(self, tmp_path: Path):
        v = WindowsRealityValidator(tmp_path)
        r = v.validate_pyqt6_lifecycle()
        assert r.passed, r.detail


class TestDeploymentRollbackReplay:
    def test_rollback(self, tmp_path: Path):
        v = WindowsRealityValidator(tmp_path)
        r = v.validate_deployment_rollback_replay()
        assert r.passed, r.detail


class TestValidateAll:
    def test_all_windows_scenarios(self, tmp_path: Path):
        v = WindowsRealityValidator(tmp_path)
        results = v.validate_all()
        assert len(results) == 11
        passed = sum(1 for r in results if r.passed)
        assert passed >= 10, f"passed={passed}/11: {[r.scenario for r in results if not r.passed]}"

    def test_each_has_duration(self, tmp_path: Path):
        v = WindowsRealityValidator(tmp_path)
        for r in v.validate_all():
            assert r.duration_seconds >= 0
