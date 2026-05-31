from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from typing import Any


class AlertSeverity(Enum):
    INFO = auto()
    WARNING = auto()
    ERROR = auto()
    CRITICAL = auto()


class AlertCategory(Enum):
    CORRUPTION = auto()
    WAL_RECOVERY = auto()
    SYNC_CONFLICT = auto()
    RECOVERY_EVENT = auto()
    MEMORY_PRESSURE = auto()
    SAFE_MODE = auto()
    SYSTEM_ERROR = auto()
    OPERATION_BLOCKED = auto()


@dataclass
class Alert:
    alert_id: str
    category: AlertCategory
    severity: AlertSeverity = AlertSeverity.INFO
    title: str = ""
    message: str = ""
    detail: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    acknowledged: bool = False
    acknowledged_at: datetime | None = None
    auto_dismiss_seconds: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_critical(self) -> bool:
        return self.severity == AlertSeverity.CRITICAL

    def acknowledge(self) -> None:
        self.acknowledged = True
        self.acknowledged_at = datetime.now(timezone.utc)


class AlertService:
    MAX_ALERTS = 200

    def __init__(self) -> None:
        self._alerts: list[Alert] = []
        self._dismiss_callbacks: dict[str, list[Any]] = {}

    @property
    def alert_count(self) -> int:
        return len(self._alerts)

    def push(self, alert: Alert) -> None:
        if len(self._alerts) >= self.MAX_ALERTS:
            self._alerts.pop(0)
        self._alerts.append(alert)

    def create_alert(
        self, category: AlertCategory, title: str,
        message: str, severity: AlertSeverity = AlertSeverity.INFO,
        **kwargs: Any,
    ) -> Alert:
        alert_id = f"{category.name}_{datetime.now(timezone.utc).timestamp()}"
        alert = Alert(
            alert_id=alert_id, category=category, severity=severity,
            title=title, message=message, **kwargs,
        )
        self.push(alert)
        return alert

    def acknowledge(self, alert_id: str) -> bool:
        for alert in self._alerts:
            if alert.alert_id == alert_id:
                alert.acknowledge()
                return True
        return False

    def acknowledge_all(self) -> int:
        count = 0
        for alert in self._alerts:
            if not alert.acknowledged:
                alert.acknowledge()
                count += 1
        return count

    @property
    def unacknowledged(self) -> list[Alert]:
        return [a for a in self._alerts if not a.acknowledged]

    @property
    def critical_alerts(self) -> list[Alert]:
        return [a for a in self._alerts if a.is_critical and not a.acknowledged]

    def get_by_category(self, category: AlertCategory) -> list[Alert]:
        return [a for a in self._alerts if a.category == category]

    def clear_acknowledged(self) -> int:
        before = len(self._alerts)
        self._alerts = [a for a in self._alerts if not a.acknowledged]
        return before - len(self._alerts)

    def clear_all(self) -> None:
        self._alerts.clear()

    def recent(self, n: int = 20) -> list[Alert]:
        return self._alerts[-n:]

    def corruption_warning(self, component: str, detail: str = "") -> Alert:
        return self.create_alert(
            AlertCategory.CORRUPTION, f"Corruption detected: {component}",
            detail or f"Potential corruption in {component}",
            severity=AlertSeverity.CRITICAL,
        )

    def wal_recovery_alert(self, message: str) -> Alert:
        return self.create_alert(
            AlertCategory.WAL_RECOVERY, "WAL Recovery",
            message, severity=AlertSeverity.WARNING,
        )

    def sync_conflict_alert(self, detail: str) -> Alert:
        return self.create_alert(
            AlertCategory.SYNC_CONFLICT, "Sync Conflict",
            detail, severity=AlertSeverity.WARNING,
        )

    def memory_pressure_alert(self, memory_mb: float, max_mb: int) -> Alert:
        return self.create_alert(
            AlertCategory.MEMORY_PRESSURE, "Memory Pressure",
            f"Memory at {memory_mb:.0f} MB of {max_mb} MB limit",
            severity=AlertSeverity.WARNING,
        )

    def safe_mode_alert(self, reason: str) -> Alert:
        return self.create_alert(
            AlertCategory.SAFE_MODE, "Safe Mode Active",
            reason, severity=AlertSeverity.WARNING,
        )
