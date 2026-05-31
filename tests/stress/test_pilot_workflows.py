from __future__ import annotations

from pathlib import Path

from app.core.stress.pilot_workflows import PilotWorkflowValidator


class TestCorrespondenceLifecycle:
    def test_lifecycle(self, tmp_path: Path):
        v = PilotWorkflowValidator(tmp_path)
        r = v.validate_correspondence_lifecycle()
        assert r.passed, r.detail


class TestSaveInterruption:
    def test_save_interrupt(self, tmp_path: Path):
        v = PilotWorkflowValidator(tmp_path)
        r = v.validate_save_interruption()
        assert r.passed, r.detail


class TestOperatorSwitching:
    def test_switching(self, tmp_path: Path):
        v = PilotWorkflowValidator(tmp_path)
        r = v.validate_operator_switching()
        assert r.passed, r.detail


class TestDuplicateSubmissions:
    def test_duplicates(self, tmp_path: Path):
        v = PilotWorkflowValidator(tmp_path)
        r = v.validate_duplicate_submissions()
        assert r.passed, r.detail


class TestArchiveOverload:
    def test_overload(self, tmp_path: Path):
        v = PilotWorkflowValidator(tmp_path)
        r = v.validate_archive_overload()
        assert r.passed, r.detail


class TestInvalidAttachmentRejection:
    def test_attachment_rejection(self, tmp_path: Path):
        v = PilotWorkflowValidator(tmp_path)
        r = v.validate_invalid_attachment_rejection()
        assert r.passed, r.detail


class TestConcurrentNumbering:
    def test_numbering(self, tmp_path: Path):
        v = PilotWorkflowValidator(tmp_path)
        r = v.validate_concurrent_numbering()
        assert r.passed, r.detail


class TestSessionRecovery:
    def test_recovery(self, tmp_path: Path):
        v = PilotWorkflowValidator(tmp_path)
        r = v.validate_session_recovery()
        assert r.passed, r.detail


class TestOperatorRollback:
    def test_rollback(self, tmp_path: Path):
        v = PilotWorkflowValidator(tmp_path)
        r = v.validate_operator_rollback()
        assert r.passed, r.detail


class TestValidateAll:
    def test_all_pilot_workflows(self, tmp_path: Path):
        v = PilotWorkflowValidator(tmp_path)
        results = v.validate_all()
        assert len(results) == 9
        passed = sum(1 for r in results if r.passed)
        assert passed >= 8, f"passed={passed}/9: {[r.scenario for r in results if not r.passed]}"

    def test_each_has_duration(self, tmp_path: Path):
        v = PilotWorkflowValidator(tmp_path)
        for r in v.validate_all():
            assert r.duration_seconds >= 0
