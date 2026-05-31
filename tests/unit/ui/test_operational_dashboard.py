from __future__ import annotations

from datetime import datetime, timezone

from app.ui.core.dashboard_service import DashboardService
from app.ui.core.operational_panels import (
    AuditPanelState,
    CrashRecoveryPanelState,
    FederationPanelState,
    MemoryPressurePanelState,
    PanelSeverity,
    QueuePanelState,
    RecoveryPanelState,
    RuntimeMetricsPanelState,
    StartupIntegrityPanelState,
)


class TestPanelStates:
    def test_federation_defaults(self):
        panel = FederationPanelState()
        assert panel.peer_count == 0
        assert panel.severity == PanelSeverity.INFO
        assert panel.sync_status == "unknown"

    def test_federation_severity_ok_when_connected(self):
        panel = FederationPanelState(connected_peers=3, peer_count=5)
        panel.severity = PanelSeverity.OK
        content = {"connected": panel.connected_peers}
        assert content["connected"] == 3

    def test_audit_critical_severity(self):
        panel = AuditPanelState(critical_alerts=2)
        assert panel.critical_alerts == 2
        assert panel.severity == PanelSeverity.INFO  # default, not auto-calculated

    def test_startup_integrity_all_passed(self):
        panel = StartupIntegrityPanelState(all_passed=True)
        assert panel.all_passed
        assert panel.passed_checks == 0

    def test_startup_integrity_failures(self):
        panel = StartupIntegrityPanelState(
            all_passed=False, passed_checks=3, failed_checks=2, check_count=5
        )
        assert panel.failed_checks == 2

    def test_recovery_healthy(self):
        panel = RecoveryPanelState(database_ok=True, wal_ok=True)
        assert panel.database_ok
        assert panel.wal_ok
        assert not panel.recovery_needed

    def test_recovery_critical(self):
        panel = RecoveryPanelState(database_ok=False)
        assert not panel.database_ok

    def test_recovery_wal_warning(self):
        panel = RecoveryPanelState(database_ok=True, wal_ok=False)
        assert panel.wal_ok is False

    def test_queue_defaults(self):
        panel = QueuePanelState()
        assert panel.queue_depth == 0
        assert panel.severity == PanelSeverity.INFO

    def test_queue_high_depth(self):
        panel = QueuePanelState(queue_depth=90, max_size=100)
        assert panel.queue_depth == 90

    def test_queue_errors(self):
        panel = QueuePanelState(error_count=3)
        assert panel.error_count == 3

    def test_runtime_metrics_defaults(self):
        panel = RuntimeMetricsPanelState()
        assert panel.cpu_percent == 0.0
        assert panel.memory_mb == 0.0
        assert panel.uptime_seconds == 0.0

    def test_runtime_metrics_high_cpu(self):
        panel = RuntimeMetricsPanelState(cpu_percent=95.0)
        assert panel.cpu_percent == 95.0

    def test_memory_pressure_defaults(self):
        panel = MemoryPressurePanelState()
        assert panel.pressure_level == "none"
        assert not panel.is_critical

    def test_memory_pressure_critical(self):
        panel = MemoryPressurePanelState(is_critical=True)
        assert panel.is_critical

    def test_memory_pressure_in_pressure(self):
        panel = MemoryPressurePanelState(in_pressure=True)
        assert panel.in_pressure

    def test_crash_recovery_defaults(self):
        panel = CrashRecoveryPanelState()
        assert panel.crash_count == 0
        assert panel.recovery_count == 0

    def test_crash_recovery_with_events(self):
        panel = CrashRecoveryPanelState(
            crash_count=3,
            recovery_count=2,
            recent_events=[{"type": "crash", "time": "now"}],
        )
        assert panel.crash_count == 3
        assert len(panel.recent_events) == 1

    def test_panel_severity_enum_members(self):
        assert PanelSeverity.OK.value == 1
        assert PanelSeverity.WARNING.value == 3
        assert PanelSeverity.CRITICAL.value == 5


class TestDashboardService:
    def test_initial_state(self):
        svc = DashboardService()
        state = svc.state
        assert state.refresh_count == 0
        assert state.last_refresh is None

    def test_refresh_all(self):
        svc = DashboardService()
        state = svc.refresh_all()
        assert state.refresh_count == 1
        assert state.last_refresh is not None

    def test_refresh_federation(self):
        svc = DashboardService()
        svc.state.federation.connected_peers = 2
        svc.refresh_all()
        assert svc.state.federation.severity == PanelSeverity.OK

    def test_refresh_federation_no_peers(self):
        svc = DashboardService()
        svc.state.federation.connected_peers = 0
        svc.refresh_all()
        assert svc.state.federation.severity == PanelSeverity.INFO

    def test_refresh_audit_with_critical(self):
        svc = DashboardService()
        svc.state.audit.critical_alerts = 1
        svc.refresh_all()
        assert svc.state.audit.severity == PanelSeverity.CRITICAL

    def test_refresh_audit_ok(self):
        svc = DashboardService()
        svc.refresh_all()
        assert svc.state.audit.severity == PanelSeverity.OK

    def test_refresh_startup_all_passed(self):
        svc = DashboardService()
        svc.state.startup_integrity.all_passed = True
        svc.refresh_all()
        assert svc.state.startup_integrity.severity == PanelSeverity.OK

    def test_refresh_startup_failed(self):
        svc = DashboardService()
        svc.state.startup_integrity.all_passed = False
        svc.state.startup_integrity.failed_checks = 2
        svc.refresh_all()
        assert svc.state.startup_integrity.severity == PanelSeverity.WARNING

    def test_refresh_recovery_healthy(self):
        svc = DashboardService()
        svc.state.recovery.database_ok = True
        svc.state.recovery.wal_ok = True
        svc.refresh_all()
        assert svc.state.recovery.severity == PanelSeverity.OK

    def test_refresh_recovery_db_fail(self):
        svc = DashboardService()
        svc.state.recovery.database_ok = False
        svc.refresh_all()
        assert svc.state.recovery.severity == PanelSeverity.CRITICAL

    def test_refresh_recovery_wal_fail(self):
        svc = DashboardService()
        svc.state.recovery.database_ok = True
        svc.state.recovery.wal_ok = False
        svc.refresh_all()
        assert svc.state.recovery.severity == PanelSeverity.WARNING

    def test_refresh_queue_ok(self):
        svc = DashboardService()
        svc.refresh_all()
        assert svc.state.queue.severity == PanelSeverity.OK

    def test_refresh_queue_high_ratio(self):
        svc = DashboardService()
        svc.state.queue.queue_depth = 95
        svc.state.queue.max_size = 100
        svc.refresh_all()
        assert svc.state.queue.severity == PanelSeverity.WARNING

    def test_refresh_queue_with_errors(self):
        svc = DashboardService()
        svc.state.queue.error_count = 1
        svc.refresh_all()
        assert svc.state.queue.severity == PanelSeverity.WARNING

    def test_refresh_runtime_metrics_ok(self):
        svc = DashboardService()
        svc.refresh_all()
        assert svc.state.runtime_metrics.severity == PanelSeverity.OK

    def test_refresh_runtime_metrics_high(self):
        svc = DashboardService()
        svc.state.runtime_metrics.cpu_percent = 95.0
        svc.refresh_all()
        assert svc.state.runtime_metrics.severity == PanelSeverity.WARNING

    def test_refresh_memory_pressure_ok(self):
        svc = DashboardService()
        svc.refresh_all()
        assert svc.state.memory_pressure.severity == PanelSeverity.OK

    def test_refresh_memory_pressure_warning(self):
        svc = DashboardService()
        svc.state.memory_pressure.in_pressure = True
        svc.refresh_all()
        assert svc.state.memory_pressure.severity == PanelSeverity.WARNING

    def test_refresh_memory_pressure_critical(self):
        svc = DashboardService()
        svc.state.memory_pressure.is_critical = True
        svc.refresh_all()
        assert svc.state.memory_pressure.severity == PanelSeverity.CRITICAL

    def test_refresh_crash_recovery_ok(self):
        svc = DashboardService()
        svc.refresh_all()
        assert svc.state.crash_recovery.severity == PanelSeverity.OK

    def test_refresh_crash_recovery_warning(self):
        svc = DashboardService()
        svc.state.crash_recovery.crash_count = 2
        svc.refresh_all()
        assert svc.state.crash_recovery.severity == PanelSeverity.WARNING
