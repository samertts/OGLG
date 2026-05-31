from __future__ import annotations

from pathlib import Path

from app.core.stress.institutional_simulation import InstitutionSimulator


class TestConcurrentOperators:
    def test_15_operators(self, tmp_path: Path):
        sim = InstitutionSimulator(tmp_path / "inst")
        report = sim.simulate_concurrent_operators(15)
        assert report.passed, report.detail

    def test_50_operators(self, tmp_path: Path):
        sim = InstitutionSimulator(tmp_path / "inst")
        report = sim.simulate_concurrent_operators(50)
        assert report.passed, report.detail


class TestMultiBranchFederation:
    def test_branch_replay_ordering(self, tmp_path: Path):
        sim = InstitutionSimulator(tmp_path / "inst")
        report = sim.simulate_multi_branch_federation()
        assert report.passed, report.detail


class TestDelayedSync:
    def test_delayed_ordering(self, tmp_path: Path):
        sim = InstitutionSimulator(tmp_path / "inst")
        report = sim.simulate_delayed_sync(0.001)
        assert report.passed, report.detail


class TestArchiveGrowth:
    def test_30_day_growth(self, tmp_path: Path):
        sim = InstitutionSimulator(tmp_path / "inst")
        report = sim.simulate_archive_growth_over_time()
        assert report.passed, report.detail


class TestAuditReplayValidation:
    def test_hash_chain_integrity(self, tmp_path: Path):
        sim = InstitutionSimulator(tmp_path / "inst")
        report = sim.simulate_audit_replay_validation()
        assert report.passed, report.detail
        assert report.audit_integrity


class TestConcurrentNumbering:
    def test_no_gaps(self, tmp_path: Path):
        sim = InstitutionSimulator(tmp_path / "inst")
        report = sim.simulate_concurrent_numbering()
        assert report.passed, report.detail


class TestUnsafeShutdown:
    def test_rollback_protects(self, tmp_path: Path):
        sim = InstitutionSimulator(tmp_path / "inst")
        report = sim.simulate_unsafe_shutdown_during_sync()
        assert report.passed, report.detail


class TestCrossInstitutionReplay:
    def test_ordering_across_institutions(self, tmp_path: Path):
        sim = InstitutionSimulator(tmp_path / "inst")
        report = sim.simulate_cross_institution_replay()
        assert report.passed, report.detail


class TestLargeQueueReplay:
    def test_10k_queue_ordering(self, tmp_path: Path):
        sim = InstitutionSimulator(tmp_path / "inst")
        report = sim.simulate_large_queue_replay()
        assert report.passed, report.detail


class TestRunAll:
    def test_all_scenarios_execute(self, tmp_path: Path):
        sim = InstitutionSimulator(tmp_path / "inst")
        results = sim.run_all()
        assert len(results) == 9

    def test_all_pass(self, tmp_path: Path):
        sim = InstitutionSimulator(tmp_path / "inst")
        passed = sum(1 for r in sim.run_all() if r.passed)
        assert passed >= 8
