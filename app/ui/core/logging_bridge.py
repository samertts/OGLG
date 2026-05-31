from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from loguru import logger

from app.ui.core.alert_service import Alert, AlertService
from app.ui.core.safety_dialogs import (
    RollbackConfirmation,
    SafetyDialogService,
    UnsafeOperationSeverity,
)


@dataclass
class LoggingBridgeConfig:
    log_confirmations: bool = True
    log_alerts: bool = True
    log_guards: bool = True
    confirmation_level: str = "info"
    alert_level_map: dict[str, str] = field(default_factory=lambda: {
        "CRITICAL": "critical",
        "ERROR": "error",
        "WARNING": "warning",
        "INFO": "info",
    })
    guard_level_map: dict[str, str] = field(default_factory=lambda: {
        "CRITICAL": "critical",
        "HIGH": "error",
        "MEDIUM": "warning",
        "LOW": "info",
    })
    max_detail_length: int = 500


class LoggingBridge:
    def __init__(self, config: LoggingBridgeConfig | None = None) -> None:
        self._config = config or LoggingBridgeConfig()
        self._safety_service: SafetyDialogService | None = None
        self._alert_service: AlertService | None = None
        self._confirmations_logged: int = 0
        self._alerts_logged: int = 0
        self._guards_triggered: int = 0

    def bind_safety_service(self, service: SafetyDialogService) -> None:
        self._safety_service = service
        service.set_confirm_callback(self._on_confirmation)

    def bind_alert_service(self, service: AlertService) -> None:
        self._alert_service = service

    def _truncate(self, text: str) -> str:
        if len(text) > self._config.max_detail_length:
            return text[: self._config.max_detail_length] + "..."
        return text

    def _on_confirmation(self, confirmation: RollbackConfirmation) -> bool:
        if not self._config.log_confirmations:
            return False
        self._confirmations_logged += 1
        level = self._config.confirmation_level
        extra: dict[str, Any] = {
            "operation_id": confirmation.operation_id,
            "severity": confirmation.severity.name,
            "destructive": confirmation.destructive,
        }
        if confirmation.audit_context:
            extra["audit_context"] = confirmation.audit_context
        msg = f"Safety confirmation requested: {confirmation.title} — {confirmation.message}"
        log_method = getattr(logger, level, logger.info)
        log_method(self._truncate(msg), extra=extra)
        return False

    def log_guard_trigger(self, guard_id: str, severity: UnsafeOperationSeverity) -> None:
        if not self._config.log_guards:
            return
        self._guards_triggered += 1
        level = self._config.guard_level_map.get(severity.name, "warning")
        msg = f"Unsafe operation guard triggered: {guard_id} ({severity.name})"
        log_method = getattr(logger, level, logger.warning)
        log_method(msg, extra={"guard_id": guard_id, "severity": severity.name})

    def log_alert(self, alert: Alert) -> None:
        if not self._config.log_alerts:
            return
        self._alerts_logged += 1
        level = self._config.alert_level_map.get(alert.severity.name, "info")
        msg = f"Alert: [{alert.category.name}] {alert.title} — {alert.message}"
        log_method = getattr(logger, level, logger.info)
        log_method(self._truncate(msg), extra={
            "alert_id": alert.alert_id,
            "category": alert.category.name,
            "severity": alert.severity.name,
        })

    def log_alert_service_alerts(self) -> int:
        if self._alert_service is None:
            return 0
        count = 0
        for alert in self._alert_service.unacknowledged:
            self.log_alert(alert)
            count += 1
        return count

    def safe_mode_entered(self, reason: str) -> None:
        logger.critical("Safe mode entered", extra={"reason": self._truncate(reason)})

    def system_state_change(self, state_name: str, detail: str = "") -> None:
        extra: dict[str, Any] = {"state": state_name}
        if detail:
            extra["detail"] = self._truncate(detail)
        logger.info(f"System state changed to {state_name}", extra=extra)

    @property
    def confirmations_logged(self) -> int:
        return self._confirmations_logged

    @property
    def alerts_logged(self) -> int:
        return self._alerts_logged

    @property
    def guards_triggered(self) -> int:
        return self._guards_triggered
