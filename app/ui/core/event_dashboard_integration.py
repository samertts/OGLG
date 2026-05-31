from __future__ import annotations

from app.core.events.base import DomainEvent
from app.core.events.bus import EventBus
from app.ui.core.alert_service import AlertCategory, AlertService, AlertSeverity
from app.ui.core.dashboard_service import DashboardService


class EventDashboardIntegration:
    EVENT_TYPE_LETTER_CREATED = "letter.created"
    EVENT_TYPE_LETTER_UPDATED = "letter.updated"
    EVENT_TYPE_LETTER_APPROVED = "letter.approved"
    EVENT_TYPE_LETTER_REJECTED = "letter.rejected"
    EVENT_TYPE_LETTER_ARCHIVED = "letter.archived"
    EVENT_TYPE_AUTH_LOGIN = "auth.login"
    EVENT_TYPE_AUTH_LOGOUT = "auth.logout"
    EVENT_TYPE_AUTH_DENIED = "auth.denied"
    EVENT_TYPE_SYSTEM_STARTUP = "system.startup"
    EVENT_TYPE_SYSTEM_SHUTDOWN = "system.shutdown"
    EVENT_TYPE_SYSTEM_ERROR = "system.error"
    EVENT_TYPE_RECOVERY_WAL = "recovery.wal"
    EVENT_TYPE_RECOVERY_CORRUPTION = "recovery.corruption"
    EVENT_TYPE_RECOVERY_SYNC = "recovery.sync"
    EVENT_TYPE_MEMORY_PRESSURE = "memory.pressure"
    EVENT_TYPE_CRASH_OCCURRED = "crash.occurred"
    EVENT_TYPE_QUEUE_BACKLOG = "queue.backlog"

    def __init__(
        self,
        dashboard: DashboardService,
        alert_service: AlertService | None = None,
    ) -> None:
        self._dashboard = dashboard
        self._alert_service = alert_service
        self._bus: EventBus | None = None
        self._subscribed: bool = False
        self._event_counts: dict[str, int] = {}

    def bind(self, bus: EventBus) -> None:
        self._bus = bus
        self._subscribe_all()
        self._subscribed = True

    def unbind(self) -> None:
        if self._bus is not None and self._subscribed:
            for event_type in self._get_event_types():
                self._bus.unsubscribe_all(event_type)
        self._subscribed = False
        self._bus = None

    def _get_event_types(self) -> list[str]:
        return [
            self.EVENT_TYPE_LETTER_CREATED,
            self.EVENT_TYPE_LETTER_UPDATED,
            self.EVENT_TYPE_LETTER_APPROVED,
            self.EVENT_TYPE_LETTER_REJECTED,
            self.EVENT_TYPE_LETTER_ARCHIVED,
            self.EVENT_TYPE_AUTH_LOGIN,
            self.EVENT_TYPE_AUTH_LOGOUT,
            self.EVENT_TYPE_AUTH_DENIED,
            self.EVENT_TYPE_SYSTEM_STARTUP,
            self.EVENT_TYPE_SYSTEM_SHUTDOWN,
            self.EVENT_TYPE_SYSTEM_ERROR,
            self.EVENT_TYPE_RECOVERY_WAL,
            self.EVENT_TYPE_RECOVERY_CORRUPTION,
            self.EVENT_TYPE_RECOVERY_SYNC,
            self.EVENT_TYPE_MEMORY_PRESSURE,
            self.EVENT_TYPE_CRASH_OCCURRED,
            self.EVENT_TYPE_QUEUE_BACKLOG,
        ]

    def _subscribe_all(self) -> None:
        if self._bus is None:
            return
        self._bus.subscribe(self.EVENT_TYPE_LETTER_CREATED, self._on_letter_created)
        self._bus.subscribe(self.EVENT_TYPE_LETTER_UPDATED, self._on_letter_updated)
        self._bus.subscribe(self.EVENT_TYPE_LETTER_APPROVED, self._on_letter_approved)
        self._bus.subscribe(self.EVENT_TYPE_LETTER_REJECTED, self._on_letter_rejected)
        self._bus.subscribe(self.EVENT_TYPE_LETTER_ARCHIVED, self._on_letter_archived)
        self._bus.subscribe(self.EVENT_TYPE_AUTH_LOGIN, self._on_auth_event)
        self._bus.subscribe(self.EVENT_TYPE_AUTH_LOGOUT, self._on_auth_event)
        self._bus.subscribe(self.EVENT_TYPE_AUTH_DENIED, self._on_auth_denied)
        self._bus.subscribe(self.EVENT_TYPE_SYSTEM_STARTUP, self._on_system_event)
        self._bus.subscribe(self.EVENT_TYPE_SYSTEM_SHUTDOWN, self._on_system_event)
        self._bus.subscribe(self.EVENT_TYPE_SYSTEM_ERROR, self._on_system_error)
        self._bus.subscribe(self.EVENT_TYPE_RECOVERY_WAL, self._on_recovery_wal)
        self._bus.subscribe(self.EVENT_TYPE_RECOVERY_CORRUPTION, self._on_recovery_corruption)
        self._bus.subscribe(self.EVENT_TYPE_RECOVERY_SYNC, self._on_recovery_sync)
        self._bus.subscribe(self.EVENT_TYPE_MEMORY_PRESSURE, self._on_memory_pressure)
        self._bus.subscribe(self.EVENT_TYPE_CRASH_OCCURRED, self._on_crash)
        self._bus.subscribe(self.EVENT_TYPE_QUEUE_BACKLOG, self._on_queue_backlog)

    def _increment(self, event_type: str) -> None:
        self._event_counts[event_type] = self._event_counts.get(event_type, 0) + 1

    def _update_queue(self) -> None:
        panel = self._dashboard.state.queue
        panel.queue_depth = self._event_counts.get(self.EVENT_TYPE_LETTER_CREATED, 0)
        panel.completed_count = self._event_counts.get(self.EVENT_TYPE_LETTER_ARCHIVED, 0)
        dashboard = self._dashboard
        dashboard._refresh_queue()

    def _on_letter_created(self, event: DomainEvent) -> None:
        self._increment(self.EVENT_TYPE_LETTER_CREATED)
        self._update_queue()

    def _on_letter_updated(self, event: DomainEvent) -> None:
        self._increment(self.EVENT_TYPE_LETTER_UPDATED)
        self._update_queue()

    def _on_letter_approved(self, event: DomainEvent) -> None:
        self._increment(self.EVENT_TYPE_LETTER_APPROVED)
        self._update_queue()

    def _on_letter_rejected(self, event: DomainEvent) -> None:
        self._increment(self.EVENT_TYPE_LETTER_REJECTED)
        self._update_queue()

    def _on_letter_archived(self, event: DomainEvent) -> None:
        self._increment(self.EVENT_TYPE_LETTER_ARCHIVED)
        self._update_queue()

    def _on_auth_event(self, event: DomainEvent) -> None:
        key = f"auth_{event.event_type.split('.')[1]}"
        self._increment(key)

    def _on_auth_denied(self, event: DomainEvent) -> None:
        panel = self._dashboard.state.audit
        panel.warning_alerts += 1
        dashboard = self._dashboard
        dashboard._refresh_audit()
        if self._alert_service:
            self._alert_service.create_alert(
                AlertCategory.SYSTEM_ERROR, "Access Denied",
                event.data.get("reason", "Unauthorized access attempt"),
                severity=AlertSeverity.WARNING,
            )

    def _on_system_event(self, event: DomainEvent) -> None:
        panel = self._dashboard.state.startup_integrity
        if event.event_type == self.EVENT_TYPE_SYSTEM_STARTUP:
            panel.all_passed = True
            panel.mode = "normal"
        elif event.event_type == self.EVENT_TYPE_SYSTEM_SHUTDOWN:
            panel.mode = "shutdown"
        dashboard = self._dashboard
        dashboard._refresh_startup_integrity()

    def _on_system_error(self, event: DomainEvent) -> None:
        panel = self._dashboard.state.audit
        panel.critical_alerts += 1
        dashboard = self._dashboard
        dashboard._refresh_audit()
        if self._alert_service:
            self._alert_service.create_alert(
                AlertCategory.SYSTEM_ERROR, "System Error",
                event.data.get("message", "Unknown system error"),
                severity=AlertSeverity.ERROR,
            )

    def _on_recovery_wal(self, event: DomainEvent) -> None:
        panel = self._dashboard.state.recovery
        panel.wal_ok = False
        panel.recovery_needed = True
        dashboard = self._dashboard
        dashboard._refresh_recovery()
        if self._alert_service:
            self._alert_service.wal_recovery_alert(
                event.data.get("message", "WAL checkpoint issue detected"),
            )

    def _on_recovery_corruption(self, event: DomainEvent) -> None:
        panel = self._dashboard.state.recovery
        panel.database_ok = False
        panel.recovery_needed = True
        dashboard = self._dashboard
        dashboard._refresh_recovery()
        if self._alert_service:
            self._alert_service.corruption_warning(
                event.data.get("component", "unknown"),
                event.data.get("detail", ""),
            )

    def _on_recovery_sync(self, event: DomainEvent) -> None:
        panel = self._dashboard.state.federation
        panel.sync_errors += 1
        dashboard = self._dashboard
        dashboard._refresh_federation()
        if self._alert_service:
            self._alert_service.sync_conflict_alert(
                event.data.get("detail", "Sync conflict detected"),
            )

    def _on_memory_pressure(self, event: DomainEvent) -> None:
        panel = self._dashboard.state.memory_pressure
        memory_mb = event.data.get("memory_mb", 0.0)
        max_mb = event.data.get("max_mb", 1024)
        panel.memory_mb = memory_mb
        panel.max_memory_mb = max_mb
        panel.in_pressure = memory_mb > max_mb * 0.85
        panel.is_critical = memory_mb > max_mb * 0.95
        dashboard = self._dashboard
        dashboard._refresh_memory_pressure()
        if self._alert_service:
            self._alert_service.memory_pressure_alert(memory_mb, max_mb)

    def _on_crash(self, event: DomainEvent) -> None:
        panel = self._dashboard.state.crash_recovery
        panel.crash_count += 1
        panel.recent_events.append(event.data)
        if len(panel.recent_events) > 20:
            panel.recent_events.pop(0)
        dashboard = self._dashboard
        dashboard._refresh_crash_recovery()

    def _on_queue_backlog(self, event: DomainEvent) -> None:
        panel = self._dashboard.state.queue
        panel.error_count += 1
        dashboard = self._dashboard
        dashboard._refresh_queue()

    @property
    def is_bound(self) -> bool:
        return self._subscribed and self._bus is not None

    @property
    def event_counts(self) -> dict[str, int]:
        return dict(self._event_counts)

    def reset_counts(self) -> None:
        self._event_counts.clear()
