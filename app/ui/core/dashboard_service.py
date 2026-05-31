from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

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


@dataclass
class OperationalDashboardState:
    federation: FederationPanelState = field(default_factory=FederationPanelState)
    audit: AuditPanelState = field(default_factory=AuditPanelState)
    startup_integrity: StartupIntegrityPanelState = field(
        default_factory=StartupIntegrityPanelState
    )
    recovery: RecoveryPanelState = field(default_factory=RecoveryPanelState)
    queue: QueuePanelState = field(default_factory=QueuePanelState)
    runtime_metrics: RuntimeMetricsPanelState = field(default_factory=RuntimeMetricsPanelState)
    memory_pressure: MemoryPressurePanelState = field(default_factory=MemoryPressurePanelState)
    crash_recovery: CrashRecoveryPanelState = field(default_factory=CrashRecoveryPanelState)
    last_refresh: datetime | None = None
    refresh_count: int = 0


class DashboardService:
    def __init__(self) -> None:
        self._state = OperationalDashboardState()

    @property
    def state(self) -> OperationalDashboardState:
        return self._state

    def refresh_all(self) -> OperationalDashboardState:
        self._state.last_refresh = datetime.now(timezone.utc)
        self._state.refresh_count += 1

        self._refresh_federation()
        self._refresh_audit()
        self._refresh_startup_integrity()
        self._refresh_recovery()
        self._refresh_queue()
        self._refresh_runtime_metrics()
        self._refresh_memory_pressure()
        self._refresh_crash_recovery()

        return self._state

    def _refresh_federation(self) -> None:
        panel = self._state.federation
        panel.severity = PanelSeverity.OK if panel.connected_peers > 0 else PanelSeverity.INFO

    def _refresh_audit(self) -> None:
        panel = self._state.audit
        if panel.critical_alerts > 0:
            panel.severity = PanelSeverity.CRITICAL
        elif panel.warning_alerts > 0:
            panel.severity = PanelSeverity.WARNING
        else:
            panel.severity = PanelSeverity.OK

    def _refresh_startup_integrity(self) -> None:
        panel = self._state.startup_integrity
        if panel.all_passed:
            panel.severity = PanelSeverity.OK
        elif panel.failed_checks > 0:
            panel.severity = PanelSeverity.WARNING

    def _refresh_recovery(self) -> None:
        panel = self._state.recovery
        if not panel.database_ok:
            panel.severity = PanelSeverity.CRITICAL
        elif not panel.wal_ok:
            panel.severity = PanelSeverity.WARNING
        elif panel.recovery_needed:
            panel.severity = PanelSeverity.WARNING
        else:
            panel.severity = PanelSeverity.OK

    def _refresh_queue(self) -> None:
        panel = self._state.queue
        ratio = panel.queue_depth / panel.max_size if panel.max_size > 0 else 0
        if panel.error_count > 0:
            panel.severity = PanelSeverity.WARNING
        elif ratio > 0.8:
            panel.severity = PanelSeverity.WARNING
        else:
            panel.severity = PanelSeverity.OK

    def _refresh_runtime_metrics(self) -> None:
        panel = self._state.runtime_metrics
        if panel.cpu_percent > 90 or panel.memory_mb > 900:
            panel.severity = PanelSeverity.WARNING
        else:
            panel.severity = PanelSeverity.OK

    def _refresh_memory_pressure(self) -> None:
        panel = self._state.memory_pressure
        if panel.is_critical:
            panel.severity = PanelSeverity.CRITICAL
        elif panel.in_pressure:
            panel.severity = PanelSeverity.WARNING
        else:
            panel.severity = PanelSeverity.OK

    def _refresh_crash_recovery(self) -> None:
        panel = self._state.crash_recovery
        if panel.crash_count > 0:
            panel.severity = PanelSeverity.WARNING
        else:
            panel.severity = PanelSeverity.OK
