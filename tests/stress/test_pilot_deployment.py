from __future__ import annotations

from pathlib import Path

from app.core.stress.pilot_deployment import PilotDeploymentValidator


class TestControlledInstitutionalRollout:
    def test_rollout(self, tmp_path: Path):
        v = PilotDeploymentValidator(tmp_path)
        r = v.validate_controlled_institutional_rollout()
        assert r.passed, r.detail


class TestPilotDeploymentProcedures:
    def test_procedures(self, tmp_path: Path):
        v = PilotDeploymentValidator(tmp_path)
        r = v.validate_pilot_deployment_procedures()
        assert r.passed, r.detail


class TestDeploymentVerificationChecklists:
    def test_checklists(self, tmp_path: Path):
        v = PilotDeploymentValidator(tmp_path)
        r = v.validate_deployment_verification_checklists()
        assert r.passed, r.detail


class TestRollbackSafeDeployment:
    def test_rollback_safe(self, tmp_path: Path):
        v = PilotDeploymentValidator(tmp_path)
        r = v.validate_rollback_safe_deployment()
        assert r.passed, r.detail


class TestInstallerIntegrityVerification:
    def test_installer_integrity(self, tmp_path: Path):
        v = PilotDeploymentValidator(tmp_path)
        r = v.validate_installer_integrity_verification()
        assert r.passed, r.detail


class TestEnvironmentCompatibility:
    def test_env_compat(self, tmp_path: Path):
        v = PilotDeploymentValidator(tmp_path)
        r = v.validate_environment_compatibility()
        assert r.passed, r.detail


class TestLowResourceWorkstationDeployment:
    def test_low_resource(self, tmp_path: Path):
        v = PilotDeploymentValidator(tmp_path)
        r = v.validate_low_resource_workstation_deployment()
        assert r.passed, r.detail


class TestOfflineDeploymentVerification:
    def test_offline(self, tmp_path: Path):
        v = PilotDeploymentValidator(tmp_path)
        r = v.validate_offline_deployment_verification()
        assert r.passed, r.detail


class TestDeploymentReplayValidation:
    def test_deploy_replay(self, tmp_path: Path):
        v = PilotDeploymentValidator(tmp_path)
        r = v.validate_deployment_replay_validation()
        assert r.passed, r.detail


class TestDeterministicStartupValidation:
    def test_startup(self, tmp_path: Path):
        v = PilotDeploymentValidator(tmp_path)
        r = v.validate_deterministic_startup_validation()
        assert r.passed, r.detail


class TestValidateAll:
    def test_all_pilot_deployment(self, tmp_path: Path):
        v = PilotDeploymentValidator(tmp_path)
        results = v.validate_all()
        assert len(results) == 10
        passed = sum(1 for r in results if r.passed)
        assert passed >= 9, f"passed={passed}/10: {[r.scenario for r in results if not r.passed]}"

    def test_each_has_duration(self, tmp_path: Path):
        v = PilotDeploymentValidator(tmp_path)
        for r in v.validate_all():
            assert r.duration_seconds >= 0
