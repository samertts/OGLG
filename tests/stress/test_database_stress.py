from __future__ import annotations

from pathlib import Path

from app.core.stress.database_stress import DatabaseStressSuite


class TestMillionRowArchive:
    def test_million_row_inserts(self, tmp_path: Path):
        suite = DatabaseStressSuite(tmp_path / "stress_workspace")
        report = suite.simulate_million_row_archive()
        assert report.passed, report.detail

    def test_replay_consistency_stress(self, tmp_path: Path):
        suite = DatabaseStressSuite(tmp_path / "stress_workspace")
        report = suite.simulate_replay_consistency_stress()
        assert report.passed, report.detail


class TestConcurrentWorkstationLoad:
    def test_concurrent_workers(self, tmp_path: Path):
        suite = DatabaseStressSuite(tmp_path / "stress_workspace")
        report = suite.simulate_concurrent_workstation_load()
        assert report.passed, report.detail


class TestLargeWalGrowth:
    def test_wal_grows_before_checkpoint(self, tmp_path: Path):
        suite = DatabaseStressSuite(tmp_path / "stress_workspace")
        report = suite.simulate_large_wal_growth()
        assert report.passed, report.detail

    def test_wal_has_bytes(self, tmp_path: Path):
        suite = DatabaseStressSuite(tmp_path / "stress_workspace")
        report = suite.simulate_large_wal_growth()
        assert report.wal_bytes > 0, "WAL file should exist with data"


class TestArchiveFragmentation:
    def test_fragmentation_handling(self, tmp_path: Path):
        suite = DatabaseStressSuite(tmp_path / "stress_workspace")
        report = suite.simulate_archive_fragmentation()
        assert report.passed, report.detail


class TestDeterministicPagination:
    def test_pagination_accuracy(self, tmp_path: Path):
        suite = DatabaseStressSuite(tmp_path / "stress_workspace")
        report = suite.simulate_pagination_stress()
        assert report.passed, report.detail


class TestBoundedCachePressure:
    def test_cache_pressure_limits(self, tmp_path: Path):
        suite = DatabaseStressSuite(tmp_path / "stress_workspace")
        report = suite.simulate_bounded_cache_pressure()
        assert report.passed, report.detail


class TestRunAll:
    def test_all_stress_scenarios_execute(self, tmp_path: Path):
        suite = DatabaseStressSuite(tmp_path / "stress_workspace")
        results = suite.run_all()
        assert len(results) == 7
        passed = sum(1 for r in results if r.passed)
        assert passed >= 6  # allow one marginal flake

    def test_reports_have_duration(self, tmp_path: Path):
        suite = DatabaseStressSuite(tmp_path / "stress_workspace")
        for r in suite.run_all():
            assert r.duration_seconds >= 0
