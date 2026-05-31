from __future__ import annotations

from app.core.chaos.operator_simulator import OperatorSimulator


class TestRapidDraftCycles:
    def test_rapid_draft_passes(self):
        s = OperatorSimulator()
        report = s.simulate_rapid_draft_cycles(50)
        assert report.success

    def test_rollback_safe(self):
        s = OperatorSimulator()
        report = s.simulate_rapid_draft_cycles(50)
        assert report.rollback_safe


class TestArchiveDropRestore:
    def test_bounded_archives(self):
        s = OperatorSimulator()
        report = s.simulate_archive_drop_restore(3)
        assert report.success
        assert report.bounded

    def test_unbounded_archives(self):
        s = OperatorSimulator()
        report = s.simulate_archive_drop_restore(10)
        assert not report.bounded


class TestRepeatedSaveSpam:
    def test_bounded_saves(self):
        s = OperatorSimulator()
        report = s.simulate_repeated_save_spam(100)
        assert report.success
        assert report.bounded

    def test_unbounded_saves(self):
        s = OperatorSimulator()
        report = s.simulate_repeated_save_spam(200)
        assert not report.bounded


class TestInterruptedPrint:
    def test_interrupted_workflow(self):
        s = OperatorSimulator()
        report = s.simulate_interrupted_print(["draft", "print", "cancel"])
        assert report.success
        assert report.rollback_safe

    def test_no_interruption(self):
        s = OperatorSimulator()
        report = s.simulate_interrupted_print(["draft", "print"])
        assert not report.success


class TestUnsafeShutdown:
    def test_no_active_drafts(self):
        s = OperatorSimulator()
        report = s.simulate_unsafe_shutdown(0)
        assert report.safe_recovery

    def test_active_drafts_unsafe(self):
        s = OperatorSimulator()
        report = s.simulate_unsafe_shutdown(5)
        assert not report.rollback_safe


class TestConcurrentOperators:
    def test_bounded_operators(self):
        s = OperatorSimulator()
        report = s.simulate_concurrent_operators(10)
        assert report.bounded

    def test_unbounded_operators(self):
        s = OperatorSimulator()
        report = s.simulate_concurrent_operators(15)
        assert not report.bounded


class TestInvalidAttachment:
    def test_oversized_rejected(self):
        s = OperatorSimulator()
        report = s.simulate_invalid_attachment(size_mb=500)
        assert report.success
        assert "500" in report.detail

    def test_unsanctioned_mime(self):
        s = OperatorSimulator()
        report = s.simulate_invalid_attachment(size_mb=10, mime="application/x-hack")
        assert report.success

    def test_valid_attachment_allowed(self):
        s = OperatorSimulator()
        report = s.simulate_invalid_attachment(size_mb=10, mime="application/pdf")
        assert not report.success


class TestOversizedArchive:
    def test_archive_within_limits(self):
        s = OperatorSimulator()
        report = s.simulate_oversized_archive(5000)
        assert report.success

    def test_archive_exceeds_limit(self):
        s = OperatorSimulator()
        report = s.simulate_oversized_archive(15000)
        assert not report.success


class TestSyncConflict:
    def test_force_unlink_resolves(self):
        s = OperatorSimulator()
        report = s.simulate_sync_conflict(force_unlink=True)
        assert report.success
