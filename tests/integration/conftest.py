"""Integration test fixtures for UI governance + core wiring."""

from __future__ import annotations

from typing import Any

import pytest

from app.core.events.bus import EventBus
from app.ui.core.alert_service import AlertService
from app.ui.core.app_state_controller import AppStateController, AppSystemState
from app.ui.core.dashboard_service import DashboardService
from app.ui.core.event_dashboard_integration import EventDashboardIntegration
from app.ui.core.logging_bridge import LoggingBridge
from app.ui.core.safety_dialogs import SafetyDialogService


@pytest.fixture
def ui_dashboard() -> DashboardService:
    return DashboardService()


@pytest.fixture
def ui_alert_service() -> AlertService:
    return AlertService()


@pytest.fixture
def ui_safety_service() -> SafetyDialogService:
    return SafetyDialogService()


@pytest.fixture
def ui_app_state() -> AppStateController:
    ctrl = AppStateController()
    ctrl.system_state = AppSystemState.NORMAL
    return ctrl


@pytest.fixture
def ui_event_bus() -> EventBus:
    return EventBus()


@pytest.fixture
def ui_logging_bridge() -> LoggingBridge:
    return LoggingBridge()


@pytest.fixture
def ui_full_stack(
    ui_dashboard: DashboardService,
    ui_alert_service: AlertService,
    ui_safety_service: SafetyDialogService,
    ui_event_bus: EventBus,
    ui_logging_bridge: LoggingBridge,
) -> dict[str, Any]:
    integration = EventDashboardIntegration(ui_dashboard, ui_alert_service)
    integration.bind(ui_event_bus)
    ui_logging_bridge.bind_safety_service(ui_safety_service)
    ui_logging_bridge.bind_alert_service(ui_alert_service)
    return {
        "dashboard": ui_dashboard,
        "alerts": ui_alert_service,
        "safety": ui_safety_service,
        "bus": ui_event_bus,
        "logging": ui_logging_bridge,
        "integration": integration,
    }
