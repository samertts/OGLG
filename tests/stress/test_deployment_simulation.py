from __future__ import annotations

from pathlib import Path

from app.core.stress.deployment_simulation import DeploymentSimulator


class TestMinistryDeployment:
    def test_ministry(self, tmp_path: Path):
        s = DeploymentSimulator(tmp_path)
        r = s.simulate_ministry()
        assert r.passed, r.detail


class TestUniversityDeployment:
    def test_university(self, tmp_path: Path):
        s = DeploymentSimulator(tmp_path)
        r = s.simulate_university()
        assert r.passed, r.detail


class TestHospitalDeployment:
    def test_hospital(self, tmp_path: Path):
        s = DeploymentSimulator(tmp_path)
        r = s.simulate_hospital()
        assert r.passed, r.detail


class TestMunicipalityDeployment:
    def test_municipality(self, tmp_path: Path):
        s = DeploymentSimulator(tmp_path)
        r = s.simulate_municipality()
        assert r.passed, r.detail


class TestLowConnectivityFederation:
    def test_federation(self, tmp_path: Path):
        s = DeploymentSimulator(tmp_path)
        r = s.simulate_low_connectivity_federation()
        assert r.passed, r.detail


class TestCrossInstitutionSync:
    def test_sync_replay(self, tmp_path: Path):
        s = DeploymentSimulator(tmp_path)
        r = s.simulate_cross_institution_sync()
        assert r.passed, r.detail


class TestOperatorContention:
    def test_contention(self, tmp_path: Path):
        s = DeploymentSimulator(tmp_path)
        r = s.simulate_operator_contention()
        assert r.passed, r.detail


class TestDelayedSync:
    def test_delayed_sync(self, tmp_path: Path):
        s = DeploymentSimulator(tmp_path)
        r = s.simulate_delayed_sync()
        assert r.passed, r.detail


class TestUnsafeShutdown:
    def test_unsafe_shutdown(self, tmp_path: Path):
        s = DeploymentSimulator(tmp_path)
        r = s.simulate_unsafe_shutdown()
        assert r.passed, r.detail


class TestValidateAll:
    def test_all_deployment_scenarios(self, tmp_path: Path):
        s = DeploymentSimulator(tmp_path)
        results = s.validate_all()
        assert len(results) == 9
        passed = sum(1 for r in results if r.passed)
        assert passed >= 8, f"passed={passed}/9: {[r.scenario for r in results if not r.passed]}"

    def test_each_has_duration(self, tmp_path: Path):
        s = DeploymentSimulator(tmp_path)
        for r in s.validate_all():
            assert r.duration_seconds >= 0
