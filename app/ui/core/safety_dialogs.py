from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from typing import Any, Callable


class UnsafeOperationSeverity(Enum):
    LOW = auto()
    MEDIUM = auto()
    HIGH = auto()
    CRITICAL = auto()


@dataclass
class RollbackConfirmation:
    operation_id: str
    title: str = ""
    message: str = ""
    detail: str = ""
    severity: UnsafeOperationSeverity = UnsafeOperationSeverity.MEDIUM
    confirm_text: str = "Confirm"
    cancel_text: str = "Cancel"
    destructive: bool = False
    requires_reason: bool = False
    audit_context: dict[str, Any] = field(default_factory=dict)

    @property
    def is_critical(self) -> bool:
        return self.severity in (
            UnsafeOperationSeverity.HIGH,
            UnsafeOperationSeverity.CRITICAL,
        )


@dataclass
class UnsafeOperationGuard:
    guard_id: str
    operation_name: str = ""
    severity: UnsafeOperationSeverity = UnsafeOperationSeverity.MEDIUM
    required_approval: bool = True
    blocking: bool = True
    cooldown_seconds: float = 0.0
    last_triggered: datetime | None = None
    trigger_count: int = 0
    handler: Callable[[], bool] | None = None

    def should_block(self) -> bool:
        if not self.blocking:
            return False
        if self.cooldown_seconds > 0 and self.last_triggered:
            elapsed = (datetime.now(timezone.utc) - self.last_triggered).total_seconds()
            if elapsed < self.cooldown_seconds:
                return False
        return True

    def record_trigger(self) -> None:
        self.last_triggered = datetime.now(timezone.utc)
        self.trigger_count += 1


class SafetyDialogService:
    def __init__(self) -> None:
        self._guards: dict[str, UnsafeOperationGuard] = {}
        self._confirmations: list[RollbackConfirmation] = []
        self._confirm_callback: Callable[[RollbackConfirmation], bool] | None = None
        self._max_confirmations = 100

    def register_guard(self, guard: UnsafeOperationGuard) -> None:
        self._guards[guard.guard_id] = guard

    def get_guard(self, guard_id: str) -> UnsafeOperationGuard | None:
        return self._guards.get(guard_id)

    def check_operation(self, guard_id: str) -> bool:
        guard = self._guards.get(guard_id)
        if guard is None:
            return True
        if guard.should_block():
            guard.record_trigger()
            if guard.handler:
                return guard.handler()
            return False
        return True

    def request_confirmation(self, confirmation: RollbackConfirmation) -> bool:
        if len(self._confirmations) >= self._max_confirmations:
            return False
        self._confirmations.append(confirmation)
        if self._confirm_callback:
            return self._confirm_callback(confirmation)
        return True

    def set_confirm_callback(self, callback: Callable[[RollbackConfirmation], bool]) -> None:
        self._confirm_callback = callback

    @property
    def pending_confirmations(self) -> list[RollbackConfirmation]:
        return list(self._confirmations)

    def resolve_confirmation(self, operation_id: str, accepted: bool) -> bool:
        for i, c in enumerate(self._confirmations):
            if c.operation_id == operation_id:
                self._confirmations.pop(i)
                return accepted
        return False

    def clear(self) -> None:
        self._guards.clear()
        self._confirmations.clear()
