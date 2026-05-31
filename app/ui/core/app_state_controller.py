from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any


class AppSystemState(Enum):
    STARTING = auto()
    NORMAL = auto()
    SAFE_MODE = auto()
    RECOVERY = auto()
    DEGRADED = auto()
    SHUTDOWN = auto()


class ScreenAccess(Enum):
    GRANTED = auto()
    DENIED = auto()
    CONDITIONAL = auto()


@dataclass
class AuthGate:
    required_roles: tuple[str, ...] = ()
    require_active: bool = True
    require_verified: bool = False

    def evaluate(self, roles: tuple[str, ...], active: bool, verified: bool = False) -> bool:
        if self.require_active and not active:
            return False
        if self.require_verified and not verified:
            return False
        if self.required_roles:
            return any(r in roles for r in self.required_roles)
        return True


@dataclass
class ScreenAvailabilityRule:
    screen_id: str
    title: str
    category: str = "main"
    order: int = 0
    auth_gate: AuthGate | None = None
    allowed_system_states: tuple[AppSystemState, ...] = (
        AppSystemState.NORMAL,
        AppSystemState.DEGRADED,
    )
    requires_workflow_completion: tuple[str, ...] = ()
    requires_system_check: str | None = None
    hidden_when_denied: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


class AppStateController:
    SCREENS: dict[str, ScreenAvailabilityRule] = {
        "dashboard": ScreenAvailabilityRule(
            screen_id="dashboard", title="Dashboard",
            category="main", order=0,
        ),
        "letter_editor": ScreenAvailabilityRule(
            screen_id="letter_editor", title="Letter Editor",
            category="correspondence", order=1,
            auth_gate=AuthGate(required_roles=("editor", "approver", "admin")),
        ),
        "archive_browser": ScreenAvailabilityRule(
            screen_id="archive_browser", title="Archive",
            category="records", order=2,
            auth_gate=AuthGate(required_roles=("viewer", "editor", "approver", "admin")),
        ),
        "search": ScreenAvailabilityRule(
            screen_id="search", title="Search",
            category="records", order=3,
            auth_gate=AuthGate(required_roles=("viewer", "editor", "approver", "admin")),
        ),
        "user_management": ScreenAvailabilityRule(
            screen_id="user_management", title="User Management",
            category="administration", order=4,
            auth_gate=AuthGate(required_roles=("admin",)),
        ),
        "settings": ScreenAvailabilityRule(
            screen_id="settings", title="Settings",
            category="administration", order=5,
            auth_gate=AuthGate(required_roles=("admin",)),
        ),
        "backup": ScreenAvailabilityRule(
            screen_id="backup", title="Backup & Recovery",
            category="administration", order=6,
            auth_gate=AuthGate(required_roles=("admin",)),
            allowed_system_states=(
                AppSystemState.NORMAL, AppSystemState.DEGRADED,
                AppSystemState.SAFE_MODE, AppSystemState.RECOVERY,
            ),
        ),
        "diagnostics": ScreenAvailabilityRule(
            screen_id="diagnostics", title="Diagnostics",
            category="system", order=7,
            auth_gate=AuthGate(required_roles=("admin",)),
            allowed_system_states=(AppSystemState.NORMAL, AppSystemState.DEGRADED),
        ),
        "runtime_health": ScreenAvailabilityRule(
            screen_id="runtime_health", title="Runtime Health",
            category="system", order=8,
            auth_gate=AuthGate(required_roles=("admin",)),
        ),
        "about": ScreenAvailabilityRule(
            screen_id="about", title="About",
            category="system", order=9,
        ),
    }

    def __init__(self) -> None:
        self._system_state: AppSystemState = AppSystemState.STARTING
        self._user_roles: tuple[str, ...] = ()
        self._user_active: bool = False
        self._user_verified: bool = False
        self._completed_workflows: set[str] = set()
        self._system_checks: dict[str, bool] = {}
        self._rules: dict[str, ScreenAvailabilityRule] = dict(self.SCREENS)

    @property
    def system_state(self) -> AppSystemState:
        return self._system_state

    @system_state.setter
    def system_state(self, state: AppSystemState) -> None:
        self._system_state = state

    def set_user_context(
        self, roles: tuple[str, ...], active: bool, verified: bool = False,
    ) -> None:
        self._user_roles = roles
        self._user_active = active
        self._user_verified = verified

    def set_system_check(self, check_name: str, passed: bool) -> None:
        self._system_checks[check_name] = passed

    def complete_workflow(self, workflow_name: str) -> None:
        self._completed_workflows.add(workflow_name)

    def register_rule(self, rule: ScreenAvailabilityRule) -> None:
        self._rules[rule.screen_id] = rule

    def get_rule(self, screen_id: str) -> ScreenAvailabilityRule | None:
        return self._rules.get(screen_id)

    def is_screen_available(self, screen_id: str) -> ScreenAccess:
        rule = self._rules.get(screen_id)
        if rule is None:
            return ScreenAccess.DENIED

        if rule.allowed_system_states and self._system_state not in rule.allowed_system_states:
            return ScreenAccess.DENIED

        if rule.auth_gate:
            if not rule.auth_gate.evaluate(
                self._user_roles, self._user_active, self._user_verified,
            ):
                return ScreenAccess.DENIED

        for workflow_name in rule.requires_workflow_completion:
            if workflow_name not in self._completed_workflows:
                return ScreenAccess.CONDITIONAL

        if rule.requires_system_check:
            if not self._system_checks.get(rule.requires_system_check, False):
                return ScreenAccess.CONDITIONAL

        return ScreenAccess.GRANTED

    @property
    def available_screens(self) -> list[ScreenAvailabilityRule]:
        return [
            r for r in sorted(self._rules.values(), key=lambda x: x.order)
            if self.is_screen_available(r.screen_id) == ScreenAccess.GRANTED
        ]

    @property
    def conditional_screens(self) -> list[ScreenAvailabilityRule]:
        return [
            r for r in sorted(self._rules.values(), key=lambda x: x.order)
            if self.is_screen_available(r.screen_id) == ScreenAccess.CONDITIONAL
        ]

    @property
    def inaccessible_screens(self) -> list[ScreenAvailabilityRule]:
        return [
            r for r in sorted(self._rules.values(), key=lambda x: x.order)
            if self.is_screen_available(r.screen_id) == ScreenAccess.DENIED
        ]

    def get_screens_by_category(self, category: str) -> list[ScreenAvailabilityRule]:
        return [r for r in self._rules.values() if r.category == category]

    def can_navigate_to(self, screen_id: str) -> bool:
        return self.is_screen_available(screen_id) in (
            ScreenAccess.GRANTED, ScreenAccess.CONDITIONAL,
        )

    def reset(self) -> None:
        self._system_state = AppSystemState.STARTING
        self._user_roles = ()
        self._user_active = False
        self._user_verified = False
        self._completed_workflows.clear()
        self._system_checks.clear()
