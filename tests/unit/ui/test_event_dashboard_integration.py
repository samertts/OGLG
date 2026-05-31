from __future__ import annotations

from app.core.events.base import DomainEvent, EventMetadata
from app.core.events.bus import EventBus
from app.ui.core.alert_service import AlertService
from app.ui.core.dashboard_service import DashboardService
from app.ui.core.event_dashboard_integration import EventDashboardIntegration


def _make_event(event_type: str, data: dict | None = None) -> DomainEvent:
    return DomainEvent(
        aggregate_id="test",
        event_type=event_type,
        data=data or {},
        metadata=EventMetadata(),
    )


class TestEventDashboardIntegration:
    def test_initial_state(self):
        dashboard = DashboardService()
        integration = EventDashboardIntegration(dashboard)
        assert not integration.is_bound
        assert integration.event_counts == {}

    def test_bind_subscribes_to_bus(self):
        bus = EventBus()
        dashboard = DashboardService()
        integration = EventDashboardIntegration(dashboard)
        integration.bind(bus)
        assert integration.is_bound

    def test_unbind_removes_subscriptions(self):
        bus = EventBus()
        dashboard = DashboardService()
        integration = EventDashboardIntegration(dashboard)
        integration.bind(bus)
        integration.unbind()
        assert not integration.is_bound

    def test_letter_created_updates_queue(self):
        bus = EventBus()
        dashboard = DashboardService()
        integration = EventDashboardIntegration(dashboard)
        integration.bind(bus)
        bus.publish(_make_event(integration.EVENT_TYPE_LETTER_CREATED))
        assert dashboard.state.queue.queue_depth == 1

    def test_letter_archived_updates_completed(self):
        bus = EventBus()
        dashboard = DashboardService()
        integration = EventDashboardIntegration(dashboard)
        integration.bind(bus)
        bus.publish(_make_event(integration.EVENT_TYPE_LETTER_ARCHIVED))
        assert dashboard.state.queue.completed_count == 1

    def test_auth_denied_triggers_alert(self):
        bus = EventBus()
        dashboard = DashboardService()
        alerts = AlertService()
        integration = EventDashboardIntegration(dashboard, alerts)
        integration.bind(bus)
        bus.publish(_make_event(
            integration.EVENT_TYPE_AUTH_DENIED,
            {"reason": "Insufficient permissions"},
        ))
        assert dashboard.state.audit.warning_alerts == 1
        assert len(alerts.unacknowledged) == 1

    def test_system_startup_updates_integrity(self):
        bus = EventBus()
        dashboard = DashboardService()
        integration = EventDashboardIntegration(dashboard)
        integration.bind(bus)
        bus.publish(_make_event(integration.EVENT_TYPE_SYSTEM_STARTUP))
        assert dashboard.state.startup_integrity.all_passed

    def test_system_error_creates_alert(self):
        bus = EventBus()
        dashboard = DashboardService()
        alerts = AlertService()
        integration = EventDashboardIntegration(dashboard, alerts)
        integration.bind(bus)
        bus.publish(_make_event(
            integration.EVENT_TYPE_SYSTEM_ERROR,
            {"message": "DB connection lost"},
        ))
        assert dashboard.state.audit.critical_alerts == 1
        assert len(alerts.unacknowledged) == 1

    def test_recovery_wal_sets_panel(self):
        bus = EventBus()
        dashboard = DashboardService()
        integration = EventDashboardIntegration(dashboard)
        integration.bind(bus)
        bus.publish(_make_event(integration.EVENT_TYPE_RECOVERY_WAL))
        assert not dashboard.state.recovery.wal_ok
        assert dashboard.state.recovery.recovery_needed

    def test_recovery_corruption_sets_panel(self):
        bus = EventBus()
        dashboard = DashboardService()
        alerts = AlertService()
        integration = EventDashboardIntegration(dashboard, alerts)
        integration.bind(bus)
        bus.publish(_make_event(
            integration.EVENT_TYPE_RECOVERY_CORRUPTION,
            {"component": "archive_index", "detail": "Checksum mismatch"},
        ))
        assert not dashboard.state.recovery.database_ok

    def test_memory_pressure_updates_panel(self):
        bus = EventBus()
        dashboard = DashboardService()
        integration = EventDashboardIntegration(dashboard)
        integration.bind(bus)
        bus.publish(_make_event(
            integration.EVENT_TYPE_MEMORY_PRESSURE,
            {"memory_mb": 950.0, "max_mb": 1024},
        ))
        assert dashboard.state.memory_pressure.in_pressure

    def test_memory_critical(self):
        bus = EventBus()
        dashboard = DashboardService()
        integration = EventDashboardIntegration(dashboard)
        integration.bind(bus)
        bus.publish(_make_event(
            integration.EVENT_TYPE_MEMORY_PRESSURE,
            {"memory_mb": 990.0, "max_mb": 1024},
        ))
        assert dashboard.state.memory_pressure.is_critical

    def test_crash_updates_panel(self):
        bus = EventBus()
        dashboard = DashboardService()
        integration = EventDashboardIntegration(dashboard)
        integration.bind(bus)
        bus.publish(_make_event(
            integration.EVENT_TYPE_CRASH_OCCURRED,
            {"component": "search_engine"},
        ))
        assert dashboard.state.crash_recovery.crash_count == 1
        assert len(dashboard.state.crash_recovery.recent_events) == 1

    def test_queue_backlog_increments_errors(self):
        bus = EventBus()
        dashboard = DashboardService()
        integration = EventDashboardIntegration(dashboard)
        integration.bind(bus)
        bus.publish(_make_event(integration.EVENT_TYPE_QUEUE_BACKLOG))
        assert dashboard.state.queue.error_count == 1

    def test_reset_counts(self):
        bus = EventBus()
        dashboard = DashboardService()
        integration = EventDashboardIntegration(dashboard)
        integration.bind(bus)
        bus.publish(_make_event(integration.EVENT_TYPE_LETTER_CREATED))
        integration.reset_counts()
        assert integration.event_counts == {}

    def test_multiple_events_accumulate(self):
        bus = EventBus()
        dashboard = DashboardService()
        integration = EventDashboardIntegration(dashboard)
        integration.bind(bus)
        for _ in range(5):
            bus.publish(_make_event(integration.EVENT_TYPE_LETTER_CREATED))
        assert dashboard.state.queue.queue_depth == 5

    def test_sync_event_updates_federation(self):
        bus = EventBus()
        dashboard = DashboardService()
        alerts = AlertService()
        integration = EventDashboardIntegration(dashboard, alerts)
        integration.bind(bus)
        bus.publish(_make_event(
            integration.EVENT_TYPE_RECOVERY_SYNC,
            {"detail": "Version mismatch"},
        ))
        assert dashboard.state.federation.sync_errors == 1
        assert len(alerts.unacknowledged) == 1
