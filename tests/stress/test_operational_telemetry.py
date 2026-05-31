from __future__ import annotations

from pathlib import Path

from app.core.stress.operational_telemetry import OperationalTelemetryValidator


class TestLocalOnlyDiagnostics:
    def test_local_diag(self, tmp_path: Path):
        v = OperationalTelemetryValidator(tmp_path)
        r = v.validate_local_only_diagnostics()
        assert r.passed, r.detail


class TestBoundedReplayMetrics:
    def test_bounded_metrics(self, tmp_path: Path):
        v = OperationalTelemetryValidator(tmp_path)
        r = v.validate_bounded_replay_metrics()
        assert r.passed, r.detail


class TestCrashSnapshotCapture:
    def test_crash_snapshot(self, tmp_path: Path):
        v = OperationalTelemetryValidator(tmp_path)
        r = v.validate_crash_snapshot_capture()
        assert r.passed, r.detail


class TestWalIncidentDiagnostics:
    def test_wal_incident(self, tmp_path: Path):
        v = OperationalTelemetryValidator(tmp_path)
        r = v.validate_wal_incident_diagnostics()
        assert r.passed, r.detail


class TestFederationIncidentDiagnostics:
    def test_fed_incident(self, tmp_path: Path):
        v = OperationalTelemetryValidator(tmp_path)
        r = v.validate_federation_incident_diagnostics()
        assert r.passed, r.detail


class TestArchiveIntegrityMetrics:
    def test_archive_metrics(self, tmp_path: Path):
        v = OperationalTelemetryValidator(tmp_path)
        r = v.validate_archive_integrity_metrics()
        assert r.passed, r.detail


class TestMemoryGrowthDiagnostics:
    def test_mem_growth(self, tmp_path: Path):
        v = OperationalTelemetryValidator(tmp_path)
        r = v.validate_memory_growth_diagnostics()
        assert r.passed, r.detail


class TestResourceExhaustionCapture:
    def test_resource_exhaust(self, tmp_path: Path):
        v = OperationalTelemetryValidator(tmp_path)
        r = v.validate_resource_exhaustion_capture()
        assert r.passed, r.detail


class TestDeterministicOperationalLogging:
    def test_op_logging(self, tmp_path: Path):
        v = OperationalTelemetryValidator(tmp_path)
        r = v.validate_deterministic_operational_logging()
        assert r.passed, r.detail


class TestOfflineIncidentExportBundles:
    def test_incident_export(self, tmp_path: Path):
        v = OperationalTelemetryValidator(tmp_path)
        r = v.validate_offline_incident_export_bundles()
        assert r.passed, r.detail


class TestIncidentSeverityClassification:
    def test_severity(self, tmp_path: Path):
        v = OperationalTelemetryValidator(tmp_path)
        r = v.validate_incident_severity_classification()
        assert r.passed, r.detail


class TestDeterministicIncidentEscalation:
    def test_escalation(self, tmp_path: Path):
        v = OperationalTelemetryValidator(tmp_path)
        r = v.validate_deterministic_incident_escalation()
        assert r.passed, r.detail


class TestValidateAll:
    def test_all_telemetry(self, tmp_path: Path):
        v = OperationalTelemetryValidator(tmp_path)
        results = v.validate_all()
        assert len(results) == 12
        passed = sum(1 for r in results if r.passed)
        assert passed >= 11, f"passed={passed}/12: {[r.scenario for r in results if not r.passed]}"

    def test_each_has_duration(self, tmp_path: Path):
        v = OperationalTelemetryValidator(tmp_path)
        for r in v.validate_all():
            assert r.duration_seconds >= 0
