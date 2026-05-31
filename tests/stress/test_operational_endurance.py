from __future__ import annotations

from pathlib import Path

from app.core.stress.operational_endurance import OperationalEnduranceValidator


class TestMultiWeekOperationalReplay:
    def test_multi_week(self, tmp_path: Path):
        v = OperationalEnduranceValidator(tmp_path)
        r = v.validate_multi_week_operational_replay()
        assert r.passed, r.detail


class TestLongSessionSurvivability:
    def test_long_session(self, tmp_path: Path):
        v = OperationalEnduranceValidator(tmp_path)
        r = v.validate_long_session_survivability()
        assert r.passed, r.detail


class TestRepeatedRecoveryCycle:
    def test_recovery_cycle(self, tmp_path: Path):
        v = OperationalEnduranceValidator(tmp_path)
        r = v.validate_repeated_recovery_cycle()
        assert r.passed, r.detail


class TestArchiveGrowthObservation:
    def test_archive_growth(self, tmp_path: Path):
        v = OperationalEnduranceValidator(tmp_path)
        r = v.validate_archive_growth_observation()
        assert r.passed, r.detail


class TestFederationContinuityObservation:
    def test_fed_continuity(self, tmp_path: Path):
        v = OperationalEnduranceValidator(tmp_path)
        r = v.validate_federation_continuity_observation()
        assert r.passed, r.detail


class TestLowResourceEndurance:
    def test_low_resource(self, tmp_path: Path):
        v = OperationalEnduranceValidator(tmp_path)
        r = v.validate_low_resource_endurance()
        assert r.passed, r.detail


class TestOperatorContentionObservation:
    def test_contention(self, tmp_path: Path):
        v = OperationalEnduranceValidator(tmp_path)
        r = v.validate_operator_contention_observation()
        assert r.passed, r.detail


class TestDeterministicReplayVerification:
    def test_det_replay(self, tmp_path: Path):
        v = OperationalEnduranceValidator(tmp_path)
        r = v.validate_deterministic_replay_verification()
        assert r.passed, r.detail


class TestBoundedResourceVerification:
    def test_bounded_resource(self, tmp_path: Path):
        v = OperationalEnduranceValidator(tmp_path)
        r = v.validate_bounded_resource_verification()
        assert r.passed, r.detail


class TestFinalOperationalDivergenceDetection:
    def test_divergence(self, tmp_path: Path):
        v = OperationalEnduranceValidator(tmp_path)
        r = v.validate_final_operational_divergence_detection()
        assert r.passed, r.detail


class TestImmutableOperationalSnapshots:
    def test_snapshots(self, tmp_path: Path):
        v = OperationalEnduranceValidator(tmp_path)
        r = v.validate_immutable_operational_snapshots()
        assert r.passed, r.detail


class TestReplaySafeForensicContinuity:
    def test_forensic(self, tmp_path: Path):
        v = OperationalEnduranceValidator(tmp_path)
        r = v.validate_replay_safe_forensic_continuity()
        assert r.passed, r.detail


class TestValidateAll:
    def test_all_endurance(self, tmp_path: Path):
        v = OperationalEnduranceValidator(tmp_path)
        results = v.validate_all()
        assert len(results) == 12
        passed = sum(1 for r in results if r.passed)
        assert passed >= 11, f"passed={passed}/12: {[r.scenario for r in results if not r.passed]}"

    def test_each_has_duration(self, tmp_path: Path):
        v = OperationalEnduranceValidator(tmp_path)
        for r in v.validate_all():
            assert r.duration_seconds >= 0
