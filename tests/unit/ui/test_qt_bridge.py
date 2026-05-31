from __future__ import annotations

from app.ui.core.alert_service import AlertCategory, AlertService, AlertSeverity
from app.ui.core.app_state_controller import AppStateController, AppSystemState, ScreenAccess
from app.ui.core.qt_bridge import (
    NullAlertBridge,
    NullSafetyDialogBridge,
    NullScreenBridge,
    SafetyDialogBridgeInterface,
)
from app.ui.core.safety_dialogs import RollbackConfirmation, SafetyDialogService


class TestNullScreenBridge:
    def test_sync_availability(self):
        bridge = NullScreenBridge()
        ctrl = AppStateController()
        ctrl.system_state = AppSystemState.NORMAL
        ctrl.set_user_context(("admin",), True)
        bridge.sync_availability(ctrl)

    def test_navigate_returns_true(self):
        bridge = NullScreenBridge()
        assert bridge.navigate_to("dashboard")

    def test_on_availability_changed(self):
        bridge = NullScreenBridge()
        calls: list[tuple[str, ScreenAccess]] = []
        bridge.on_availability_changed(lambda sid, acc: calls.append((sid, acc)))
        assert len(bridge._callbacks) == 1


class TestNullAlertBridge:
    def test_show_alert_tracks(self):
        bridge = NullAlertBridge()
        svc = AlertService()
        alert = svc.corruption_warning("test")
        bridge.show_alert(alert)
        assert len(bridge.shown_alerts) == 1

    def test_dismiss_alert_removes(self):
        bridge = NullAlertBridge()
        svc = AlertService()
        alert = svc.corruption_warning("test")
        bridge.show_alert(alert)
        bridge.dismiss_alert(alert.alert_id)
        assert len(bridge.shown_alerts) == 0

    def test_show_notification_noop(self):
        bridge = NullAlertBridge()
        bridge.show_notification("Title", "Message")

    def test_bind_service(self):
        bridge = NullAlertBridge()
        svc = AlertService()
        bridge.bind_service(svc)


class TestNullSafetyDialogBridge:
    def test_show_confirmation_default_denies(self):
        bridge = NullSafetyDialogBridge()
        rc = RollbackConfirmation(operation_id="op1", title="Confirm?")
        assert not bridge.show_confirmation(rc)

    def test_auto_accept(self):
        bridge = NullSafetyDialogBridge()
        bridge._auto_accept = True
        rc = RollbackConfirmation(operation_id="op1")
        assert bridge.show_confirmation(rc)

    def test_pending_confirmations(self):
        bridge = NullSafetyDialogBridge()
        bridge.show_confirmation(RollbackConfirmation(operation_id="op1"))
        bridge.show_confirmation(RollbackConfirmation(operation_id="op2"))
        assert len(bridge.pending_confirmations) == 2

    def test_bind_service(self):
        bridge = NullSafetyDialogBridge()
        svc = SafetyDialogService()
        bridge.bind_service(svc)
        rc = RollbackConfirmation(operation_id="op1")
        svc.request_confirmation(rc)
        assert len(bridge.pending_confirmations) == 1

    def test_show_warning_noop(self):
        bridge = NullSafetyDialogBridge()
        bridge.show_warning("Title", "Message")


class TestBridgeFactories:
    def test_create_screen_bridge_default_null(self):
        from app.ui.core.qt_bridge import create_qt_screen_bridge
        bridge = create_qt_screen_bridge()
        assert isinstance(bridge, NullScreenBridge)

    def test_create_alert_bridge_default_null(self):
        from app.ui.core.qt_bridge import create_qt_alert_bridge
        bridge = create_qt_alert_bridge()
        assert isinstance(bridge, NullAlertBridge)

    def test_create_safety_dialog_bridge_default_null(self):
        from app.ui.core.qt_bridge import create_qt_safety_dialog_bridge
        bridge = create_qt_safety_dialog_bridge()
        assert isinstance(bridge, NullSafetyDialogBridge)

    def test_interface_compliance(self):
        assert issubclass(NullScreenBridge, object)
        assert issubclass(NullAlertBridge, object)
        assert issubclass(NullSafetyDialogBridge, SafetyDialogBridgeInterface)
