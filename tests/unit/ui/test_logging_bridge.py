from __future__ import annotations

from app.ui.core.alert_service import AlertCategory, AlertService, AlertSeverity
from app.ui.core.logging_bridge import LoggingBridge, LoggingBridgeConfig
from app.ui.core.safety_dialogs import (
    RollbackConfirmation,
    SafetyDialogService,
    UnsafeOperationSeverity,
)


class TestLoggingBridge:
    def test_initial_state(self):
        bridge = LoggingBridge()
        assert bridge.confirmations_logged == 0
        assert bridge.alerts_logged == 0
        assert bridge.guards_triggered == 0

    def test_bind_safety_service_sets_callback(self):
        bridge = LoggingBridge()
        svc = SafetyDialogService()
        bridge.bind_safety_service(svc)
        rc = RollbackConfirmation(operation_id="op1", title="Test")
        svc.request_confirmation(rc)
        assert bridge.confirmations_logged == 1

    def test_confirmations_logged_with_default_config(self):
        bridge = LoggingBridge()
        svc = SafetyDialogService()
        bridge.bind_safety_service(svc)
        svc.request_confirmation(RollbackConfirmation(
            operation_id="op1", title="Delete?", message="Permanently delete?",
        ))
        assert bridge.confirmations_logged == 1

    def test_confirmations_disabled(self):
        config = LoggingBridgeConfig(log_confirmations=False)
        bridge = LoggingBridge(config)
        svc = SafetyDialogService()
        bridge.bind_safety_service(svc)
        svc.request_confirmation(RollbackConfirmation(operation_id="op1"))
        assert bridge.confirmations_logged == 0

    def test_log_guard_trigger(self):
        bridge = LoggingBridge()
        bridge.log_guard_trigger("g1", UnsafeOperationSeverity.HIGH)
        assert bridge.guards_triggered == 1

    def test_guard_trigger_disabled(self):
        config = LoggingBridgeConfig(log_guards=False)
        bridge = LoggingBridge(config)
        bridge.log_guard_trigger("g1", UnsafeOperationSeverity.HIGH)
        assert bridge.guards_triggered == 0

    def test_log_alert(self):
        bridge = LoggingBridge()
        svc = AlertService()
        alert = svc.corruption_warning("archive", "Data corrupt")
        bridge.log_alert(alert)
        assert bridge.alerts_logged == 1

    def test_log_alert_disabled(self):
        config = LoggingBridgeConfig(log_alerts=False)
        bridge = LoggingBridge(config)
        svc = AlertService()
        alert = svc.corruption_warning("archive", "Data corrupt")
        bridge.log_alert(alert)
        assert bridge.alerts_logged == 0

    def test_log_alert_service_alerts(self):
        bridge = LoggingBridge()
        svc = AlertService()
        bridge.bind_alert_service(svc)
        svc.corruption_warning("archive")
        svc.wal_recovery_alert("WAL issue")
        count = bridge.log_alert_service_alerts()
        assert count == 2
        assert bridge.alerts_logged == 2

    def test_safe_mode_entered(self):
        bridge = LoggingBridge()
        bridge.safe_mode_entered("Startup checks failed")
        assert True

    def test_system_state_change(self):
        bridge = LoggingBridge()
        bridge.system_state_change("RECOVERY", "WAL checkpoint required")
        assert True

    def test_truncate_long_message(self):
        config = LoggingBridgeConfig(max_detail_length=10)
        bridge = LoggingBridge(config)
        svc = SafetyDialogService()
        bridge.bind_safety_service(svc)
        svc.request_confirmation(RollbackConfirmation(
            operation_id="op1",
            title="A" * 50,
            message="B" * 50,
        ))
        assert bridge.confirmations_logged == 1

    def test_bind_alert_service(self):
        bridge = LoggingBridge()
        svc = AlertService()
        bridge.bind_alert_service(svc)
        alert = svc.corruption_warning("test")
        bridge.log_alert(alert)
        assert bridge.alerts_logged == 1

    def test_multiple_confirmations_tracked(self):
        bridge = LoggingBridge()
        svc = SafetyDialogService()
        bridge.bind_safety_service(svc)
        for i in range(5):
            svc.request_confirmation(RollbackConfirmation(operation_id=f"op{i}"))
        assert bridge.confirmations_logged == 5

    def test_multiple_guards_tracked(self):
        bridge = LoggingBridge()
        for sev in UnsafeOperationSeverity:
            bridge.log_guard_trigger(f"g_{sev.name}", sev)
        assert bridge.guards_triggered == len(UnsafeOperationSeverity)
