from __future__ import annotations

from pathlib import Path

from app.core.stress.deployment_packages import DeploymentPackageValidator


class TestPackageSpecs:
    def test_specs(self, tmp_path: Path):
        v = DeploymentPackageValidator(tmp_path)
        r = v.validate_package_specs()
        assert r.passed, r.detail


class TestDependencyPreflight:
    def test_preflight(self, tmp_path: Path):
        v = DeploymentPackageValidator(tmp_path)
        r = v.validate_dependency_preflight()
        assert r.passed, r.detail


class TestRollbackUpgrade:
    def test_upgrade(self, tmp_path: Path):
        v = DeploymentPackageValidator(tmp_path)
        r = v.validate_rollback_upgrade()
        assert r.passed, r.detail


class TestOfflineBundle:
    def test_bundle(self, tmp_path: Path):
        v = DeploymentPackageValidator(tmp_path)
        r = v.validate_offline_bundle()
        assert r.passed, r.detail


class TestPackageFingerprinting:
    def test_fingerprinting(self, tmp_path: Path):
        v = DeploymentPackageValidator(tmp_path)
        r = v.validate_package_fingerprinting()
        assert r.passed, r.detail


class TestCorruptedDeploymentRecovery:
    def test_recovery(self, tmp_path: Path):
        v = DeploymentPackageValidator(tmp_path)
        r = v.validate_corrupted_deployment_recovery()
        assert r.passed, r.detail


class TestDiagnostics:
    def test_diagnostics(self, tmp_path: Path):
        v = DeploymentPackageValidator(tmp_path)
        r = v.validate_diagnostics()
        assert r.passed, r.detail


class TestReleaseReplay:
    def test_replay(self, tmp_path: Path):
        v = DeploymentPackageValidator(tmp_path)
        r = v.validate_release_replay()
        assert r.passed, r.detail


class TestValidateAll:
    def test_all_package_scenarios(self, tmp_path: Path):
        v = DeploymentPackageValidator(tmp_path)
        results = v.validate_all()
        assert len(results) == 8
        passed = sum(1 for r in results if r.passed)
        assert passed >= 7, f"passed={passed}/8: {[r.scenario for r in results if not r.passed]}"

    def test_each_has_duration(self, tmp_path: Path):
        v = DeploymentPackageValidator(tmp_path)
        for r in v.validate_all():
            assert r.duration_seconds >= 0
