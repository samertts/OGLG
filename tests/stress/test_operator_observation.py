from __future__ import annotations

from pathlib import Path

from app.core.stress.operator_observation import OperatorObservationValidator


class TestWorkflowObservation:
    def test_workflow_obs(self, tmp_path: Path):
        v = OperatorObservationValidator(tmp_path)
        r = v.validate_workflow_observation()
        assert r.passed, r.detail


class TestOperatorMisuseCapture:
    def test_misuse(self, tmp_path: Path):
        v = OperatorObservationValidator(tmp_path)
        r = v.validate_operator_misuse_capture()
        assert r.passed, r.detail


class TestWorkflowBottleneckDiagnostics:
    def test_bottleneck(self, tmp_path: Path):
        v = OperatorObservationValidator(tmp_path)
        r = v.validate_workflow_bottleneck_diagnostics()
        assert r.passed, r.detail


class TestArchiveBehaviorObservation:
    def test_archive_behavior(self, tmp_path: Path):
        v = OperatorObservationValidator(tmp_path)
        r = v.validate_archive_behavior_observation()
        assert r.passed, r.detail


class TestApprovalChainTimingAnalysis:
    def test_approval_timing(self, tmp_path: Path):
        v = OperatorObservationValidator(tmp_path)
        r = v.validate_approval_chain_timing_analysis()
        assert r.passed, r.detail


class TestOperatorInterruptionRecovery:
    def test_interruption(self, tmp_path: Path):
        v = OperatorObservationValidator(tmp_path)
        r = v.validate_operator_interruption_recovery()
        assert r.passed, r.detail


class TestLongSessionWorkflowObservation:
    def test_long_session(self, tmp_path: Path):
        v = OperatorObservationValidator(tmp_path)
        r = v.validate_long_session_workflow_observation()
        assert r.passed, r.detail


class TestReplayContinuityVerification:
    def test_replay_cont(self, tmp_path: Path):
        v = OperatorObservationValidator(tmp_path)
        r = v.validate_replay_continuity_verification()
        assert r.passed, r.detail


class TestOperationalAnomalyCapture:
    def test_anomaly(self, tmp_path: Path):
        v = OperatorObservationValidator(tmp_path)
        r = v.validate_operational_anomaly_capture()
        assert r.passed, r.detail


class TestDeterministicWorkflowAuditing:
    def test_audit(self, tmp_path: Path):
        v = OperatorObservationValidator(tmp_path)
        r = v.validate_deterministic_workflow_auditing()
        assert r.passed, r.detail


class TestValidateAll:
    def test_all_operator_observation(self, tmp_path: Path):
        v = OperatorObservationValidator(tmp_path)
        results = v.validate_all()
        assert len(results) == 10
        passed = sum(1 for r in results if r.passed)
        assert passed >= 9, f"passed={passed}/10: {[r.scenario for r in results if not r.passed]}"

    def test_each_has_duration(self, tmp_path: Path):
        v = OperatorObservationValidator(tmp_path)
        for r in v.validate_all():
            assert r.duration_seconds >= 0
