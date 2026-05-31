from __future__ import annotations

from pathlib import Path

from app.core.stress.final_reality import FinalRealityValidator


class TestFullDeploymentReplay:
    def test_deployment_replay(self, tmp_path: Path):
        v = FinalRealityValidator(tmp_path)
        r = v.validate_full_deployment_replay()
        assert r.passed, r.detail


class TestRepeatedCrashCycles:
    def test_crash_cycles(self, tmp_path: Path):
        v = FinalRealityValidator(tmp_path)
        r = v.validate_repeated_crash_cycles()
        assert r.passed, r.detail


class TestLongSessionEnduranceReplay:
    def test_long_endurance(self, tmp_path: Path):
        v = FinalRealityValidator(tmp_path)
        r = v.validate_long_session_endurance_replay()
        assert r.passed, r.detail


class TestWalInterruptionReplay:
    def test_wal_interrupt(self, tmp_path: Path):
        v = FinalRealityValidator(tmp_path)
        r = v.validate_wal_interruption_replay()
        assert r.passed, r.detail


class TestReplayDivergence:
    def test_divergence(self, tmp_path: Path):
        v = FinalRealityValidator(tmp_path)
        r = v.validate_replay_divergence()
        assert r.passed, r.detail


class TestDeterministicArchiveReplay:
    def test_det_archive(self, tmp_path: Path):
        v = FinalRealityValidator(tmp_path)
        r = v.validate_deterministic_archive_replay()
        assert r.passed, r.detail


class TestDeploymentRollbackReplay:
    def test_rollback(self, tmp_path: Path):
        v = FinalRealityValidator(tmp_path)
        r = v.validate_deployment_rollback_replay()
        assert r.passed, r.detail


class TestLowResourceSurvivability:
    def test_low_resource(self, tmp_path: Path):
        v = FinalRealityValidator(tmp_path)
        r = v.validate_low_resource_survivability()
        assert r.passed, r.detail


class TestFinalAuditContinuity:
    def test_audit_continuity(self, tmp_path: Path):
        v = FinalRealityValidator(tmp_path)
        r = v.validate_final_audit_continuity()
        assert r.passed, r.detail


class TestRealEnvironmentConsistency:
    def test_consistency(self, tmp_path: Path):
        v = FinalRealityValidator(tmp_path)
        r = v.validate_real_environment_consistency()
        assert r.passed, r.detail


class TestValidateAll:
    def test_all_final_reality(self, tmp_path: Path):
        v = FinalRealityValidator(tmp_path)
        results = v.validate_all()
        assert len(results) == 10
        passed = sum(1 for r in results if r.passed)
        assert passed >= 9, f"passed={passed}/10: {[r.scenario for r in results if not r.passed]}"

    def test_each_has_duration(self, tmp_path: Path):
        v = FinalRealityValidator(tmp_path)
        for r in v.validate_all():
            assert r.duration_seconds >= 0
