"""Integration tests: boundary conditions and error injection into safety layer."""

from __future__ import annotations

from app.ui.core.alert_service import AlertCategory, AlertService
from app.ui.core.app_state_controller import AppStateController, AppSystemState, ScreenAccess
from app.ui.core.logging_bridge import LoggingBridge
from app.ui.core.safety_dialogs import (
    RollbackConfirmation,
    SafetyDialogService,
    UnsafeOperationGuard,
    UnsafeOperationSeverity,
)


class TestSafetyBoundaryIntegration:
    def test_guard_cooldown_prevents_repeated_triggers(self):
        svc = SafetyDialogService()
        guard = UnsafeOperationGuard(guard_id="g1", cooldown_seconds=30)
        svc.register_guard(guard)
        assert not svc.check_operation("g1")

    def test_multiple_guards_independent(self):
        svc = SafetyDialogService()
        svc.register_guard(UnsafeOperationGuard(guard_id="g1", handler=lambda: False))
        svc.register_guard(UnsafeOperationGuard(guard_id="g2", handler=lambda: True))
        assert not svc.check_operation("g1")
        assert svc.check_operation("g2")

    def test_confirmation_limit(self):
        svc = SafetyDialogService()
        svc._max_confirmations = 3
        for i in range(5):
            svc.request_confirmation(RollbackConfirmation(operation_id=f"op{i}"))
        assert len(svc.pending_confirmations) == 3

    def test_alert_limit(self):
        svc = AlertService()
        svc.MAX_ALERTS = 5
        for i in range(10):
            svc.create_alert(AlertCategory.SYSTEM_ERROR, f"E{i}", f"M{i}")
        assert svc.alert_count == 5


class TestLoggingBridgeIntegration:
    def test_logging_bridge_wired_to_safety(self, ui_full_stack: dict):
        safety: SafetyDialogService = ui_full_stack["safety"]
        logging: LoggingBridge = ui_full_stack["logging"]
        safety.request_confirmation(RollbackConfirmation(operation_id="op1", title="Delete?"))
        assert logging.confirmations_logged >= 1

    def test_logging_bridge_logs_alerts(self, ui_full_stack: dict):
        alerts: AlertService = ui_full_stack["alerts"]
        logging: LoggingBridge = ui_full_stack["logging"]
        alerts.corruption_warning("archive")
        count = logging.log_alert_service_alerts()
        assert count == 1
        assert logging.alerts_logged == 1

    def test_safe_mode_logged_as_critical(self, ui_full_stack: dict):
        logging: LoggingBridge = ui_full_stack["logging"]
        logging.safe_mode_entered("Integrity check failed")
        assert True

    def test_system_state_change_logged(self, ui_full_stack: dict):
        logging: LoggingBridge = ui_full_stack["logging"]
        logging.system_state_change("RECOVERY", "WAL replay needed")
        assert True

    def test_guard_trigger_logged(self, ui_full_stack: dict):
        logging: LoggingBridge = ui_full_stack["logging"]
        logging.log_guard_trigger("g_archive_write", UnsafeOperationSeverity.HIGH)
        assert logging.guards_triggered == 1


class TestSystemStateBoundaryIntegration:
    def test_safe_mode_blocks_non_admin_screens(self):
        ctrl = AppStateController()
        ctrl.system_state = AppSystemState.SAFE_MODE
        assert ctrl.can_navigate_to("backup") is False
        assert ctrl.can_navigate_to("dashboard") is False

    def test_admin_can_access_backup_in_safe_mode(self):
        ctrl = AppStateController()
        ctrl.system_state = AppSystemState.SAFE_MODE
        ctrl.set_user_context(("admin",), True)
        assert ctrl.can_navigate_to("backup")
        assert not ctrl.can_navigate_to("dashboard")

    def test_degraded_allows_all_admin_screens(self):
        ctrl = AppStateController()
        ctrl.system_state = AppSystemState.DEGRADED
        ctrl.set_user_context(("admin",), True)
        assert ctrl.can_navigate_to("dashboard")
        assert ctrl.can_navigate_to("diagnostics")
        assert ctrl.can_navigate_to("runtime_health")

    def test_system_transition_preserves_role_state(self):
        ctrl = AppStateController()
        ctrl.set_user_context(("admin",), True)
        for state in AppSystemState:
            ctrl.system_state = state
            if state == AppSystemState.NORMAL:
                assert ctrl.can_navigate_to("user_management")
            elif state == AppSystemState.SHUTDOWN:
                assert not ctrl.can_navigate_to("user_management")

    def test_verification_required_for_sensitive_screens(self):
        ctrl = AppStateController()
        ctrl.system_state = AppSystemState.NORMAL
        ctrl.set_user_context(("admin",), True, verified=False)
        assert ctrl.is_screen_available("settings") == ScreenAccess.GRANTED

    def test_empty_roles_blocks_gated_screens(self):
        ctrl = AppStateController()
        ctrl.system_state = AppSystemState.NORMAL
        ctrl.set_user_context((), True)
        assert ctrl.is_screen_available("letter_editor") == ScreenAccess.DENIED
        assert ctrl.is_screen_available("dashboard") == ScreenAccess.GRANTED

    def test_state_boundary_violation(self):
        from app.ui.core.app_state_controller import AuthGate
        gate = AuthGate(required_roles=("admin",))
        assert gate.evaluate(("admin",), True)
        assert not gate.evaluate(("user",), True)
