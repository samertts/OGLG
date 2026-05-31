"""Integration tests: end-to-end event flow through EventBus into dashboard panels."""

from __future__ import annotations

from app.core.events.base import DomainEvent, EventMetadata
from app.core.events.bus import EventBus
from app.ui.core.alert_service import AlertCategory
from app.ui.core.dashboard_service import DashboardService
from app.ui.core.event_dashboard_integration import EventDashboardIntegration

LETTER_CREATED = EventDashboardIntegration.EVENT_TYPE_LETTER_CREATED
AUTH_DENIED = EventDashboardIntegration.EVENT_TYPE_AUTH_DENIED
SYSTEM_STARTUP = EventDashboardIntegration.EVENT_TYPE_SYSTEM_STARTUP
MEMORY_PRESSURE = EventDashboardIntegration.EVENT_TYPE_MEMORY_PRESSURE
RECOVERY_WAL = EventDashboardIntegration.EVENT_TYPE_RECOVERY_WAL
RECOVERY_SYNC = EventDashboardIntegration.EVENT_TYPE_RECOVERY_SYNC
RECOVERY_CORRUPTION = EventDashboardIntegration.EVENT_TYPE_RECOVERY_CORRUPTION
CRASH_OCCURRED = EventDashboardIntegration.EVENT_TYPE_CRASH_OCCURRED


def _make_event(etype: str, data: dict | None = None) -> DomainEvent:
    return DomainEvent(
        aggregate_id="int", event_type=etype,
        data=data or {}, metadata=EventMetadata(),
    )


class TestEventDashboardIntegrationE2E:
    def test_letter_created_reflects_on_dashboard(self, ui_full_stack: dict) -> None:
        bus: EventBus = ui_full_stack["bus"]
        bus.publish(_make_event(LETTER_CREATED, {"id": "L001"}))
        dashboard: DashboardService = ui_full_stack["dashboard"]
        assert dashboard.state.queue.queue_depth == 1

    def test_approval_rejection_triggers_alert(self, ui_full_stack: dict) -> None:
        bus: EventBus = ui_full_stack["bus"]
        alerts = ui_full_stack["alerts"]
        bus.publish(_make_event(AUTH_DENIED, {"reason": "Insufficient role"}))
        assert len(alerts.unacknowledged) == 1
        assert "Access Denied" in alerts.unacknowledged[0].title

    def test_corruption_event_sets_recovery_panel_and_alert(self, ui_full_stack: dict) -> None:
        bus: EventBus = ui_full_stack["bus"]
        alerts = ui_full_stack["alerts"]
        bus.publish(_make_event(RECOVERY_CORRUPTION, {"component": "index"}))
        dashboard: DashboardService = ui_full_stack["dashboard"]
        assert not dashboard.state.recovery.database_ok
        assert len(alerts.get_by_category(AlertCategory.CORRUPTION)) == 1

    def test_memory_pressure_updates_dashboard(self, ui_full_stack: dict) -> None:
        bus: EventBus = ui_full_stack["bus"]
        bus.publish(_make_event(MEMORY_PRESSURE, {"memory_mb": 960.0, "max_mb": 1024}))
        dashboard: DashboardService = ui_full_stack["dashboard"]
        assert dashboard.state.memory_pressure.in_pressure
        assert not dashboard.state.memory_pressure.is_critical

    def test_memory_critical_sets_is_critical(self, ui_full_stack: dict) -> None:
        bus: EventBus = ui_full_stack["bus"]
        bus.publish(_make_event(MEMORY_PRESSURE, {"memory_mb": 990.0, "max_mb": 1024}))
        dashboard: DashboardService = ui_full_stack["dashboard"]
        assert dashboard.state.memory_pressure.is_critical

    def test_multiple_letters_accumulate(self, ui_full_stack: dict) -> None:
        bus: EventBus = ui_full_stack["bus"]
        for i in range(10):
            bus.publish(_make_event(LETTER_CREATED, {"id": f"L{i:03d}"}))
        dashboard: DashboardService = ui_full_stack["dashboard"]
        assert dashboard.state.queue.queue_depth == 10

    def test_mixed_event_types_dont_interfere(self, ui_full_stack: dict) -> None:
        bus: EventBus = ui_full_stack["bus"]
        bus.publish(_make_event(LETTER_CREATED))
        bus.publish(_make_event(SYSTEM_STARTUP))
        bus.publish(_make_event(AUTH_DENIED, {"reason": "test"}))
        dashboard: DashboardService = ui_full_stack["dashboard"]
        assert dashboard.state.queue.queue_depth == 1
        assert dashboard.state.startup_integrity.all_passed
        assert dashboard.state.audit.warning_alerts == 1

    def test_wal_event_sets_recovery_needed(self, ui_full_stack: dict) -> None:
        bus: EventBus = ui_full_stack["bus"]
        bus.publish(_make_event(RECOVERY_WAL, {"message": "Checkpoint stalled"}))
        dashboard: DashboardService = ui_full_stack["dashboard"]
        assert not dashboard.state.recovery.wal_ok
        assert dashboard.state.recovery.recovery_needed

    def test_sync_conflict_increments_federation_errors(self, ui_full_stack: dict) -> None:
        bus: EventBus = ui_full_stack["bus"]
        bus.publish(_make_event(RECOVERY_SYNC, {"detail": "Version mismatch"}))
        dashboard: DashboardService = ui_full_stack["dashboard"]
        assert dashboard.state.federation.sync_errors == 1

    def test_crash_event_tracked_in_panel(self, ui_full_stack: dict) -> None:
        bus: EventBus = ui_full_stack["bus"]
        bus.publish(_make_event(CRASH_OCCURRED, {"component": "search"}))
        dashboard: DashboardService = ui_full_stack["dashboard"]
        assert dashboard.state.crash_recovery.crash_count == 1
        assert len(dashboard.state.crash_recovery.recent_events) == 1
