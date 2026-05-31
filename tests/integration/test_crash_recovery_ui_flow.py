"""Crash-recovery UI flow: simulate crash, verify recovery panel, safety service, WAL state."""

from __future__ import annotations

from app.core.events.base import DomainEvent, EventMetadata
from app.core.events.bus import EventBus
from app.ui.core.alert_service import AlertCategory, AlertService
from app.ui.core.app_state_controller import AppStateController, AppSystemState
from app.ui.core.dashboard_service import DashboardService
from app.ui.core.event_dashboard_integration import EventDashboardIntegration
from app.ui.core.safety_dialogs import (
    RollbackConfirmation,
    SafetyDialogService,
    UnsafeOperationGuard,
    UnsafeOperationSeverity,
)
from app.ui.core.wal_safe_transitions import (
    TransitionVerdict,
    WalSafeTransitionCoordinator,
    WalState,
)


class TestCrashRecoveryUIFlow:
    def test_crash_triggers_recovery_panel_update(self):
        dashboard = DashboardService()
        bus = EventBus()
        integration = EventDashboardIntegration(dashboard)
        integration.bind(bus)

        bus.publish(DomainEvent(
            aggregate_id="system",
            event_type=integration.EVENT_TYPE_CRASH_OCCURRED,
            data={"component": "letter_editor", "memory_mb": 980},
            metadata=EventMetadata(),
        ))

        assert dashboard.state.crash_recovery.crash_count == 1
        assert len(dashboard.state.crash_recovery.recent_events) == 1
        assert dashboard.state.crash_recovery.recent_events[0]["component"] == "letter_editor"

    def test_multiple_crashes_accumulate(self):
        dashboard = DashboardService()
        bus = EventBus()
        integration = EventDashboardIntegration(dashboard)
        integration.bind(bus)

        for i in range(3):
            bus.publish(DomainEvent(
                aggregate_id="system",
                event_type=integration.EVENT_TYPE_CRASH_OCCURRED,
                data={"component": f"component_{i}", "crash_id": i},
                metadata=EventMetadata(),
            ))

        assert dashboard.state.crash_recovery.crash_count == 3

    def test_crash_safety_guard_blocks_operation(self):
        svc = SafetyDialogService()
        guard = UnsafeOperationGuard(
            guard_id="crash_sensitive_op",
            severity=UnsafeOperationSeverity.CRITICAL,
        )
        svc.register_guard(guard)
        assert not svc.check_operation("crash_sensitive_op")

    def test_crash_safety_guard_handler_bypass(self):
        svc = SafetyDialogService()
        guard = UnsafeOperationGuard(
            guard_id="crash_sensitive_op",
            handler=lambda: True,
        )
        svc.register_guard(guard)
        assert svc.check_operation("crash_sensitive_op")

    def test_wal_state_transitions_after_crash(self):
        coord = WalSafeTransitionCoordinator()
        assert coord.wal_state == WalState.HEALTHY

        coord.set_wal_state(WalState.RECOVERING)
        assert coord.wal_state == WalState.RECOVERING

        verdict = coord.can_transition("dashboard", "backup")
        assert verdict == TransitionVerdict.BLOCKED
        coord.record_transition("dashboard", "backup", blocked=True, reason="WAL recovery")

        coord.set_wal_state(WalState.HEALTHY)
        assert coord.can_transition("dashboard", "backup") == TransitionVerdict.ALLOWED
        assert coord.blocked_count == 1

    def test_recovery_alert_generated(self):
        alerts = AlertService()
        alert = alerts.wal_recovery_alert("WAL checkpoint required after crash")
        assert alert.category.name == "WAL_RECOVERY"
        assert alert.severity.name == "WARNING"

    def test_system_state_transition_after_crash(self):
        ctrl = AppStateController()
        ctrl.set_user_context(("admin",), True)

        ctrl.system_state = AppSystemState.RECOVERY
        assert ctrl.system_state == AppSystemState.RECOVERY
        assert not ctrl.can_navigate_to("diagnostics")
        assert ctrl.can_navigate_to("backup")

        ctrl.system_state = AppSystemState.NORMAL
        assert ctrl.can_navigate_to("diagnostics")

    def test_crash_during_operation_prompts_confirmation(self):
        svc = SafetyDialogService()

        rc = RollbackConfirmation(
            operation_id="crash_op",
            title="Recovery Required",
            message="The last operation crashed. Rollback?",
            severity=UnsafeOperationSeverity.CRITICAL,
            destructive=True,
        )
        svc.request_confirmation(rc)
        pending = svc.pending_confirmations
        assert len(pending) == 1
        assert pending[0].is_critical
        assert pending[0].destructive

    def test_crash_sets_safe_mode(self):
        ctrl = AppStateController()
        ctrl.set_user_context(("admin",), True)
        ctrl.system_state = AppSystemState.SAFE_MODE

        assert ctrl.can_navigate_to("backup")
        assert not ctrl.can_navigate_to("dashboard")
        assert not ctrl.can_navigate_to("letter_editor")

    def test_crash_recovery_full_cycle(self):
        dashboard = DashboardService()
        alerts = AlertService()
        bus = EventBus()
        integration = EventDashboardIntegration(dashboard, alerts)
        integration.bind(bus)

        bus.publish(DomainEvent(
            aggregate_id="system",
            event_type=integration.EVENT_TYPE_RECOVERY_CORRUPTION,
            data={"component": "db_index", "detail": "Page integrity check failed"},
            metadata=EventMetadata(),
        ))

        assert not dashboard.state.recovery.database_ok
        assert dashboard.state.recovery.recovery_needed
        assert len(alerts.get_by_category(AlertCategory.CORRUPTION)) == 1

    def test_rollback_confirmation_audit_context(self):
        rc = RollbackConfirmation(
            operation_id="rollback_001",
            title="Rollback Letter",
            message="Rollback letter L-2024-089?",
            severity=UnsafeOperationSeverity.HIGH,
            destructive=True,
            requires_reason=True,
            audit_context={"letter_id": "L-2024-089", "user": "admin"},
        )
        assert rc.audit_context["letter_id"] == "L-2024-089"
        assert rc.requires_reason

    def test_crash_alert_acknowledge(self):
        alerts = AlertService()
        alert = alerts.corruption_warning("archive", "Checksum mismatch")
        alert_id = alert.alert_id
        assert not alert.acknowledged
        alerts.acknowledge(alert_id)
        assert alert.acknowledged
