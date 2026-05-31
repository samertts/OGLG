from __future__ import annotations

from pathlib import Path

from app.core.stress.operator_endurance import OperatorEnduranceValidator


class TestThirtyDayOperatorReplay:
    def test_thirty_day(self, tmp_path: Path):
        v = OperatorEnduranceValidator(tmp_path)
        r = v.validate_thirty_day_operator_replay()
        assert r.passed, r.detail


class TestRepeatedDraftInterruptions:
    def test_draft_interrupt(self, tmp_path: Path):
        v = OperatorEnduranceValidator(tmp_path)
        r = v.validate_repeated_draft_interruptions()
        assert r.passed, r.detail


class TestRapidConcurrentSaveReplay:
    def test_rapid_save(self, tmp_path: Path):
        v = OperatorEnduranceValidator(tmp_path)
        r = v.validate_rapid_concurrent_save_replay()
        assert r.passed, r.detail


class TestApprovalArchiveContention:
    def test_contention(self, tmp_path: Path):
        v = OperatorEnduranceValidator(tmp_path)
        r = v.validate_approval_archive_contention()
        assert r.passed, r.detail


class TestPrintInterruptionReplay:
    def test_print_interrupt(self, tmp_path: Path):
        v = OperatorEnduranceValidator(tmp_path)
        r = v.validate_print_interruption_replay()
        assert r.passed, r.detail


class TestDuplicateWorkflowRecovery:
    def test_duplicate(self, tmp_path: Path):
        v = OperatorEnduranceValidator(tmp_path)
        r = v.validate_duplicate_workflow_recovery()
        assert r.passed, r.detail


class TestInvalidAttachmentHandling:
    def test_invalid_attachment(self, tmp_path: Path):
        v = OperatorEnduranceValidator(tmp_path)
        r = v.validate_invalid_attachment_handling()
        assert r.passed, r.detail


class TestOperatorSessionRecovery:
    def test_session_recovery(self, tmp_path: Path):
        v = OperatorEnduranceValidator(tmp_path)
        r = v.validate_operator_session_recovery()
        assert r.passed, r.detail


class TestArchiveOverloadRecovery:
    def test_overload(self, tmp_path: Path):
        v = OperatorEnduranceValidator(tmp_path)
        r = v.validate_archive_overload_recovery()
        assert r.passed, r.detail


class TestReplayContinuity:
    def test_continuity(self, tmp_path: Path):
        v = OperatorEnduranceValidator(tmp_path)
        r = v.validate_replay_continuity()
        assert r.passed, r.detail


class TestValidateAll:
    def test_all_operator_endurance(self, tmp_path: Path):
        v = OperatorEnduranceValidator(tmp_path)
        results = v.validate_all()
        assert len(results) == 10
        passed = sum(1 for r in results if r.passed)
        assert passed >= 9, f"passed={passed}/10: {[r.scenario for r in results if not r.passed]}"

    def test_each_has_duration(self, tmp_path: Path):
        v = OperatorEnduranceValidator(tmp_path)
        for r in v.validate_all():
            assert r.duration_seconds >= 0
