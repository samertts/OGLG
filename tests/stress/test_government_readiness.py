from __future__ import annotations

from pathlib import Path

from app.core.stress.government_readiness import GovernmentReadinessValidator


class TestMinistryWorkflow:
    def test_full_ministry_workflow(self, tmp_path: Path):
        v = GovernmentReadinessValidator(tmp_path / "gov")
        report = v.validate_ministry_workflow()
        assert report.passed, report.detail


class TestArchiveDepartment:
    def test_archive_operations(self, tmp_path: Path):
        v = GovernmentReadinessValidator(tmp_path / "gov")
        report = v.validate_archive_department()
        assert report.passed, report.detail


class TestLaboratoryWorkflow:
    def test_lab_workflow(self, tmp_path: Path):
        v = GovernmentReadinessValidator(tmp_path / "gov")
        report = v.validate_laboratory_workflow()
        assert report.passed, report.detail


class TestMunicipalityDeployment:
    def test_low_resource_deploy(self, tmp_path: Path):
        v = GovernmentReadinessValidator(tmp_path / "gov")
        report = v.validate_municipality_deployment()
        assert report.passed, report.detail


class TestLowConnectivityFederation:
    def test_delayed_sync(self, tmp_path: Path):
        v = GovernmentReadinessValidator(tmp_path / "gov")
        report = v.validate_low_connectivity_federation()
        assert report.passed, report.detail


class TestLowResourceWorkstation:
    def test_minimal_hardware(self, tmp_path: Path):
        v = GovernmentReadinessValidator(tmp_path / "gov")
        report = v.validate_low_resource_workstation()
        assert report.passed, report.detail


class Test30DayReplay:
    def test_month_long_replay(self, tmp_path: Path):
        v = GovernmentReadinessValidator(tmp_path / "gov")
        report = v.validate_30_day_replay()
        assert report.passed, report.detail


class TestDeploymentRecovery:
    def test_crash_then_recover(self, tmp_path: Path):
        v = GovernmentReadinessValidator(tmp_path / "gov")
        report = v.validate_deployment_recovery()
        assert report.passed, report.detail


class TestCorruptionSurvival:
    def test_corruption_detected(self, tmp_path: Path):
        v = GovernmentReadinessValidator(tmp_path / "gov")
        report = v.validate_corruption_survival()
        assert report.scenario == "corruption_survival"


class TestFinalDeterministicReplay:
    def test_deterministic_ordering(self, tmp_path: Path):
        v = GovernmentReadinessValidator(tmp_path / "gov")
        report = v.validate_final_deterministic_replay()
        assert report.passed, report.detail


class TestValidateAll:
    def test_all_government_readiness_scenarios(self, tmp_path: Path):
        v = GovernmentReadinessValidator(tmp_path / "gov")
        results = v.validate_all()
        assert len(results) == 10
        passed = sum(1 for r in results if r.passed)
        assert passed >= 8, f"passed={passed}/10: {[r.scenario for r in results if not r.passed]}"

    def test_each_report_has_duration(self, tmp_path: Path):
        v = GovernmentReadinessValidator(tmp_path / "gov")
        for r in v.validate_all():
            assert r.duration_seconds >= 0
