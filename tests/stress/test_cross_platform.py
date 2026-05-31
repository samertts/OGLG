from __future__ import annotations

from pathlib import Path

from app.core.cross_platform import CrossPlatformValidator


class TestWindowsCiParity:
    def test_windows_ci(self, tmp_path: Path):
        v = CrossPlatformValidator(tmp_path)
        r = v.validate_windows_ci_parity()
        assert r.passed, r.detail


class TestReplayParity:
    def test_replay_parity(self, tmp_path: Path):
        v = CrossPlatformValidator(tmp_path)
        r = v.validate_replay_parity()
        assert r.passed, r.detail


class TestWalParity:
    def test_wal_parity(self, tmp_path: Path):
        v = CrossPlatformValidator(tmp_path)
        r = v.validate_wal_parity()
        assert r.passed, r.detail


class TestDeploymentParity:
    def test_deploy_parity(self, tmp_path: Path):
        v = CrossPlatformValidator(tmp_path)
        r = v.validate_deployment_parity()
        assert r.passed, r.detail


class TestDeterministicArchiveReplay:
    def test_archive_replay(self, tmp_path: Path):
        v = CrossPlatformValidator(tmp_path)
        r = v.validate_deterministic_archive_replay()
        assert r.passed, r.detail


class TestFederationReplayParity:
    def test_fed_parity(self, tmp_path: Path):
        v = CrossPlatformValidator(tmp_path)
        r = v.validate_federation_replay_parity()
        assert r.passed, r.detail


class TestInstallerValidation:
    def test_installer(self, tmp_path: Path):
        v = CrossPlatformValidator(tmp_path)
        r = v.validate_installer_validation()
        assert r.passed, r.detail


class TestPackageVerification:
    def test_package(self, tmp_path: Path):
        v = CrossPlatformValidator(tmp_path)
        r = v.validate_package_verification()
        assert r.passed, r.detail


class TestFilesystemAtomicityReplay:
    def test_atomicity(self, tmp_path: Path):
        v = CrossPlatformValidator(tmp_path)
        r = v.validate_filesystem_atomicity_replay()
        assert r.passed, r.detail


class TestTempFileReplacement:
    def test_temp_replace(self, tmp_path: Path):
        v = CrossPlatformValidator(tmp_path)
        r = v.validate_temp_file_replacement()
        assert r.passed, r.detail


class TestNtfsRenameAtomicity:
    def test_rename_atomicity(self, tmp_path: Path):
        v = CrossPlatformValidator(tmp_path)
        r = v.validate_ntfs_rename_atomicity()
        assert r.passed, r.detail


class TestValidateAll:
    def test_all_cross_platform(self, tmp_path: Path):
        v = CrossPlatformValidator(tmp_path)
        results = v.validate_all()
        assert len(results) == 11
        passed = sum(1 for r in results if r.passed)
        assert passed >= 10, f"passed={passed}/11: {[r.scenario for r in results if not r.passed]}"

    def test_each_has_duration(self, tmp_path: Path):
        v = CrossPlatformValidator(tmp_path)
        for r in v.validate_all():
            assert r.duration_seconds >= 0
