from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Callable

from app.ui.core.alert_service import Alert, AlertService
from app.ui.core.app_state_controller import (
    AppStateController,
    ScreenAccess,
    ScreenAvailabilityRule,
)
from app.ui.core.safety_dialogs import RollbackConfirmation, SafetyDialogService


class ScreenBridgeInterface(ABC):
    @abstractmethod
    def sync_availability(self, controller: AppStateController) -> None: ...

    @abstractmethod
    def navigate_to(self, screen_id: str) -> bool: ...

    @abstractmethod
    def show_screen(self, rule: ScreenAvailabilityRule) -> None: ...

    @abstractmethod
    def hide_screen(self, screen_id: str) -> None: ...

    @abstractmethod
    def on_availability_changed(self, callback: Callable[[str, ScreenAccess], None]) -> None: ...


class AlertBridgeInterface(ABC):
    @abstractmethod
    def show_alert(self, alert: Alert) -> None: ...

    @abstractmethod
    def dismiss_alert(self, alert_id: str) -> None: ...

    @abstractmethod
    def show_notification(self, title: str, message: str, level: str = "info") -> None: ...

    @abstractmethod
    def bind_service(self, service: AlertService) -> None: ...


class SafetyDialogBridgeInterface(ABC):
    @abstractmethod
    def show_confirmation(self, confirmation: RollbackConfirmation) -> bool: ...

    @abstractmethod
    def show_warning(self, title: str, message: str, detail: str = "") -> None: ...

    @abstractmethod
    def bind_service(self, service: SafetyDialogService) -> None: ...


class NullScreenBridge(ScreenBridgeInterface):
    def __init__(self) -> None:
        self._callbacks: list[Callable[[str, ScreenAccess], None]] = []

    def sync_availability(self, controller: AppStateController) -> None:
        for screen in controller.available_screens:
            self.show_screen(screen)
        for screen in controller.inaccessible_screens:
            self.hide_screen(screen.screen_id)

    def navigate_to(self, screen_id: str) -> bool:
        return True

    def show_screen(self, rule: ScreenAvailabilityRule) -> None:
        pass

    def hide_screen(self, screen_id: str) -> None:
        pass

    def on_availability_changed(self, callback: Callable[[str, ScreenAccess], None]) -> None:
        self._callbacks.append(callback)


class NullAlertBridge(AlertBridgeInterface):
    def __init__(self) -> None:
        self._shown: list[Alert] = []

    def show_alert(self, alert: Alert) -> None:
        self._shown.append(alert)

    def dismiss_alert(self, alert_id: str) -> None:
        self._shown = [a for a in self._shown if a.alert_id != alert_id]

    def show_notification(self, title: str, message: str, level: str = "info") -> None:
        pass

    def bind_service(self, service: AlertService) -> None:
        pass

    @property
    def shown_alerts(self) -> list[Alert]:
        return list(self._shown)


class NullSafetyDialogBridge(SafetyDialogBridgeInterface):
    def __init__(self) -> None:
        self._confirmations: list[RollbackConfirmation] = []
        self._auto_accept: bool = False

    def show_confirmation(self, confirmation: RollbackConfirmation) -> bool:
        self._confirmations.append(confirmation)
        return self._auto_accept

    def show_warning(self, title: str, message: str, detail: str = "") -> None:
        pass

    def bind_service(self, service: SafetyDialogService) -> None:
        service.set_confirm_callback(self.show_confirmation)

    @property
    def pending_confirmations(self) -> list[RollbackConfirmation]:
        return list(self._confirmations)


def create_qt_screen_bridge(parent: Any = None) -> ScreenBridgeInterface:
    try:
        from app.ui.navigation.screen_router import ScreenRouter
        if isinstance(parent, ScreenRouter):
            return _QtScreenBridge(parent)
    except (ImportError, TypeError):
        pass
    return NullScreenBridge()


def create_qt_alert_bridge(parent: Any = None) -> AlertBridgeInterface:
    try:
        from PySide6.QtWidgets import QWidget
        if isinstance(parent, QWidget):
            return _QtAlertBridge(parent)
    except ImportError:
        pass
    return NullAlertBridge()


def create_qt_safety_dialog_bridge(parent: Any = None) -> SafetyDialogBridgeInterface:
    try:
        from PySide6.QtWidgets import QWidget
        if isinstance(parent, QWidget):
            return _QtSafetyDialogBridge(parent)
    except ImportError:
        pass
    return NullSafetyDialogBridge()


class _QtScreenBridge(ScreenBridgeInterface):
    def __init__(self, router: Any) -> None:
        self._router = router
        self._callbacks: list[Callable[[str, ScreenAccess], None]] = []

    def sync_availability(self, controller: AppStateController) -> None:
        for screen in controller.available_screens:
            self.show_screen(screen)
        for screen in controller.inaccessible_screens:
            self.hide_screen(screen.screen_id)

    def navigate_to(self, screen_id: str) -> bool:
        if hasattr(self._router, "navigate_to"):
            return self._router.navigate_to(screen_id)
        return False

    def show_screen(self, rule: ScreenAvailabilityRule) -> None:
        if hasattr(self._router, "registry") and hasattr(self._router.registry, "get"):
            entry = self._router.registry.get(rule.screen_id)
            if entry and hasattr(entry, "widget") and hasattr(entry.widget, "show"):
                entry.widget.show()

    def hide_screen(self, screen_id: str) -> None:
        if hasattr(self._router, "registry") and hasattr(self._router.registry, "get"):
            entry = self._router.registry.get(screen_id)
            if entry and hasattr(entry, "widget") and hasattr(entry.widget, "hide"):
                entry.widget.hide()

    def on_availability_changed(self, callback: Callable[[str, ScreenAccess], None]) -> None:
        self._callbacks.append(callback)


class _QtAlertBridge(AlertBridgeInterface):
    def __init__(self, parent_widget: Any) -> None:
        self._parent = parent_widget
        self._service: AlertService | None = None

    def show_alert(self, alert: Alert) -> None:
        try:
            from PySide6.QtWidgets import QMessageBox
            icon = (
                QMessageBox.Warning
                if alert.severity.name in ("WARNING", "ERROR")
                else QMessageBox.Information
            )
            if alert.is_critical:
                icon = QMessageBox.Critical
            box = QMessageBox(icon, alert.title, alert.message, parent=self._parent)
            box.setDetailedText(alert.detail)
            box.exec()
        except ImportError:
            pass

    def dismiss_alert(self, alert_id: str) -> None:
        if self._service:
            self._service.acknowledge(alert_id)

    def show_notification(self, title: str, message: str, level: str = "info") -> None:
        try:
            from PySide6.QtWidgets import QToolTip
            QToolTip.showText(self._parent.mapToGlobal(self._parent.rect().center()), message)
        except ImportError:
            pass

    def bind_service(self, service: AlertService) -> None:
        self._service = service


class _QtSafetyDialogBridge(SafetyDialogBridgeInterface):
    def __init__(self, parent_widget: Any) -> None:
        self._parent = parent_widget

    def show_confirmation(self, confirmation: RollbackConfirmation) -> bool:
        try:
            from PySide6.QtWidgets import QMessageBox
            icon = QMessageBox.Warning if confirmation.destructive else QMessageBox.Question
            box = QMessageBox(icon, confirmation.title, confirmation.message, parent=self._parent)
            box.setDetailedText(confirmation.detail)
            box.setStandardButtons(
                QMessageBox.Yes | QMessageBox.No
            )
            box.setDefaultButton(QMessageBox.No)
            result = box.exec()
            return result == QMessageBox.Yes
        except ImportError:
            return False

    def show_warning(self, title: str, message: str, detail: str = "") -> None:
        try:
            from PySide6.QtWidgets import QMessageBox
            box = QMessageBox(QMessageBox.Warning, title, message, parent=self._parent)
            if detail:
                box.setDetailedText(detail)
            box.exec()
        except ImportError:
            pass

    def bind_service(self, service: SafetyDialogService) -> None:
        service.set_confirm_callback(self.show_confirmation)
