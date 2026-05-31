from __future__ import annotations

from pathlib import Path

from app.core.alignment import RuntimeAlignmentValidator


class TestPythonVersion:
    def test_python(self, tmp_path: Path):
        v = RuntimeAlignmentValidator(tmp_path)
        r = v.validate_python_version()
        assert r.passed, r.detail


class TestSqliteVersion:
    def test_sqlite(self, tmp_path: Path):
        v = RuntimeAlignmentValidator(tmp_path)
        r = v.validate_sqlite_version()
        assert r.passed, r.detail


class TestWalFeatureCompat:
    def test_wal_compat(self, tmp_path: Path):
        v = RuntimeAlignmentValidator(tmp_path)
        r = v.validate_wal_feature_compat()
        assert r.passed, r.detail


class TestBusyTimeout:
    def test_busy(self, tmp_path: Path):
        v = RuntimeAlignmentValidator(tmp_path)
        r = v.validate_busy_timeout()
        assert r.passed, r.detail


class TestDeterministicRecovery:
    def test_det_recovery(self, tmp_path: Path):
        v = RuntimeAlignmentValidator(tmp_path)
        r = v.validate_deterministic_recovery()
        assert r.passed, r.detail


class TestWalPragmaEnforcement:
    def test_pragma_enforce(self, tmp_path: Path):
        v = RuntimeAlignmentValidator(tmp_path)
        r = v.validate_wal_pragma_enforcement()
        assert r.passed, r.detail


class TestMmapBoundary:
    def test_mmap(self, tmp_path: Path):
        v = RuntimeAlignmentValidator(tmp_path)
        r = v.validate_mmap_boundary()
        assert r.passed, r.detail


class TestSyncModeEnforcement:
    def test_sync_mode(self, tmp_path: Path):
        v = RuntimeAlignmentValidator(tmp_path)
        r = v.validate_sync_mode_enforcement()
        assert r.passed, r.detail


class TestDependencyCompat:
    def test_deps(self, tmp_path: Path):
        v = RuntimeAlignmentValidator(tmp_path)
        r = v.validate_dependency_compat()
        assert r.passed, r.detail


class TestRuntimeDiagnostics:
    def test_diags(self, tmp_path: Path):
        v = RuntimeAlignmentValidator(tmp_path)
        r = v.validate_runtime_diagnostics()
        assert r.passed, r.detail


class TestValidateAll:
    def test_all_alignment(self, tmp_path: Path):
        v = RuntimeAlignmentValidator(tmp_path)
        results = v.validate_all()
        assert len(results) == 10
        passed = sum(1 for r in results if r.passed)
        assert passed >= 9, f"passed={passed}/10: {[r.scenario for r in results if not r.passed]}"

    def test_each_has_duration(self, tmp_path: Path):
        v = RuntimeAlignmentValidator(tmp_path)
        for r in v.validate_all():
            assert r.duration_seconds >= 0
