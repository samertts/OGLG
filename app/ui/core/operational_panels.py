from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any


class PanelSeverity(Enum):
    OK = auto()
    INFO = auto()
    WARNING = auto()
    ERROR = auto()
    CRITICAL = auto()


@dataclass
class FederationPanelState:
    peer_count: int = 0
    connected_peers: int = 0
    last_sync: datetime | None = None
    sync_status: str = "unknown"
    pending_sync_items: int = 0
    sync_errors: int = 0
    severity: PanelSeverity = PanelSeverity.INFO

    def refresh(self) -> None:
        pass


@dataclass
class AuditPanelState:
    total_alerts: int = 0
    critical_alerts: int = 0
    warning_alerts: int = 0
    info_alerts: int = 0
    recent_entries: list[dict[str, Any]] = field(default_factory=list)
    last_audit_at: datetime | None = None
    severity: PanelSeverity = PanelSeverity.INFO


@dataclass
class StartupIntegrityPanelState:
    all_passed: bool = False
    check_count: int = 0
    passed_checks: int = 0
    failed_checks: int = 0
    mode: str = "unknown"
    duration_seconds: float = 0.0
    checks: list[dict[str, Any]] = field(default_factory=list)
    severity: PanelSeverity = PanelSeverity.INFO


@dataclass
class RecoveryPanelState:
    database_ok: bool = True
    wal_ok: bool = True
    recovery_needed: bool = False
    recovery_attempts: int = 0
    last_assessment: datetime | None = None
    recommendations: list[dict[str, Any]] = field(default_factory=list)
    severity: PanelSeverity = PanelSeverity.INFO


@dataclass
class QueuePanelState:
    queue_depth: int = 0
    max_size: int = 0
    pending_count: int = 0
    running_count: int = 0
    completed_count: int = 0
    failed_count: int = 0
    error_count: int = 0
    severity: PanelSeverity = PanelSeverity.INFO


@dataclass
class RuntimeMetricsPanelState:
    cpu_percent: float = 0.0
    memory_mb: float = 0.0
    widget_count: int = 0
    active_tasks: int = 0
    uptime_seconds: float = 0.0
    severity: PanelSeverity = PanelSeverity.INFO


@dataclass
class MemoryPressurePanelState:
    pressure_level: str = "none"
    memory_mb: float = 0.0
    max_memory_mb: int = 1024
    widget_count: int = 0
    max_widgets: int = 500
    in_pressure: bool = False
    is_critical: bool = False
    severity: PanelSeverity = PanelSeverity.INFO


@dataclass
class CrashRecoveryPanelState:
    crash_count: int = 0
    last_crash: datetime | None = None
    recovery_count: int = 0
    last_recovery: datetime | None = None
    recent_events: list[dict[str, Any]] = field(default_factory=list)
    severity: PanelSeverity = PanelSeverity.INFO
