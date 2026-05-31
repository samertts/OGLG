from __future__ import annotations

import pytest

from app.ui.core.app_state_controller import (
    AppStateController,
    AppSystemState,
    AuthGate,
    ScreenAccess,
    ScreenAvailabilityRule,
)


class TestAuthGate:
    def test_no_requirements_allows(self):
        gate = AuthGate()
        assert gate.evaluate((), True)

    def test_inactive_denies(self):
        gate = AuthGate(require_active=True)
        assert not gate.evaluate((), False)

    def test_unverified_denies(self):
        gate = AuthGate(require_verified=True)
        assert not gate.evaluate((), True, verified=False)

    def test_missing_role_denies(self):
        gate = AuthGate(required_roles=("admin",))
        assert not gate.evaluate(("editor",), True)

    def test_matching_role_allows(self):
        gate = AuthGate(required_roles=("admin", "editor"))
        assert gate.evaluate(("editor",), True)


class TestAppStateController:
    def test_initial_state(self):
        ctrl = AppStateController()
        assert ctrl.system_state == AppSystemState.STARTING

    def test_dashboard_available_during_startup(self):
        ctrl = AppStateController()
        assert ctrl.is_screen_available("dashboard") == ScreenAccess.DENIED

    def test_dashboard_available_in_normal(self):
        ctrl = AppStateController()
        ctrl.system_state = AppSystemState.NORMAL
        assert ctrl.is_screen_available("dashboard") == ScreenAccess.GRANTED

    def test_dashboard_available_in_degraded(self):
        ctrl = AppStateController()
        ctrl.system_state = AppSystemState.DEGRADED
        assert ctrl.is_screen_available("dashboard") == ScreenAccess.GRANTED

    def test_dashboard_unavailable_in_shutdown(self):
        ctrl = AppStateController()
        ctrl.system_state = AppSystemState.SHUTDOWN
        assert ctrl.is_screen_available("dashboard") == ScreenAccess.DENIED

    def test_letter_editor_requires_editor_role(self):
        ctrl = AppStateController()
        ctrl.system_state = AppSystemState.NORMAL
        assert ctrl.is_screen_available("letter_editor") == ScreenAccess.DENIED

    def test_letter_editor_allowed_with_role(self):
        ctrl = AppStateController()
        ctrl.system_state = AppSystemState.NORMAL
        ctrl.set_user_context(("editor",), True)
        assert ctrl.is_screen_available("letter_editor") == ScreenAccess.GRANTED

    def test_admin_screen_requires_admin_role(self):
        ctrl = AppStateController()
        ctrl.system_state = AppSystemState.NORMAL
        assert ctrl.is_screen_available("user_management") == ScreenAccess.DENIED
        ctrl.set_user_context(("admin",), True)
        assert ctrl.is_screen_available("user_management") == ScreenAccess.GRANTED

    def test_backup_available_in_recovery(self):
        ctrl = AppStateController()
        ctrl.system_state = AppSystemState.RECOVERY
        ctrl.set_user_context(("admin",), True)
        assert ctrl.is_screen_available("backup") == ScreenAccess.GRANTED

    def test_diagnostics_denied_in_recovery(self):
        ctrl = AppStateController()
        ctrl.system_state = AppSystemState.RECOVERY
        ctrl.set_user_context(("admin",), True)
        assert ctrl.is_screen_available("diagnostics") == ScreenAccess.DENIED

    def test_about_always_available(self):
        ctrl = AppStateController()
        ctrl.system_state = AppSystemState.NORMAL
        assert ctrl.is_screen_available("about") == ScreenAccess.GRANTED

    def test_unknown_screen_denied(self):
        ctrl = AppStateController()
        assert ctrl.is_screen_available("nonexistent") == ScreenAccess.DENIED

    def test_available_screens_list(self):
        ctrl = AppStateController()
        ctrl.system_state = AppSystemState.NORMAL
        ctrl.set_user_context(("admin",), True)
        screens = ctrl.available_screens
        assert len(screens) >= 9

    def test_available_screens_excludes_denied(self):
        ctrl = AppStateController()
        ctrl.system_state = AppSystemState.NORMAL
        ctrl.set_user_context(("viewer",), True)
        screen_ids = [s.screen_id for s in ctrl.available_screens]
        assert "user_management" not in screen_ids
        assert "settings" not in screen_ids

    def test_conditional_screens_list(self):
        ctrl = AppStateController()
        ctrl.system_state = AppSystemState.NORMAL
        ctrl.set_user_context(("admin",), True)
        rule = ctrl.get_rule("diagnostics")
        assert rule is not None
        rule.requires_workflow_completion = ("startup_checks",)
        assert ctrl.is_screen_available("diagnostics") == ScreenAccess.CONDITIONAL
        ctrl.complete_workflow("startup_checks")
        assert ctrl.is_screen_available("diagnostics") == ScreenAccess.GRANTED

    def test_system_check_conditional(self):
        ctrl = AppStateController()
        ctrl.system_state = AppSystemState.NORMAL
        ctrl.set_user_context(("admin",), True)
        rule = ctrl.get_rule("runtime_health")
        assert rule is not None
        rule.requires_system_check = "db_connected"
        assert ctrl.is_screen_available("runtime_health") == ScreenAccess.CONDITIONAL
        ctrl.set_system_check("db_connected", True)
        assert ctrl.is_screen_available("runtime_health") == ScreenAccess.GRANTED

    def test_can_navigate_grants_access(self):
        ctrl = AppStateController()
        ctrl.system_state = AppSystemState.NORMAL
        assert ctrl.can_navigate_to("dashboard")

    def test_can_navigate_denies_when_blocked(self):
        ctrl = AppStateController()
        assert not ctrl.can_navigate_to("dashboard")

    def test_register_rule(self):
        ctrl = AppStateController()
        rule = ScreenAvailabilityRule(
            screen_id="custom", title="Custom",
            auth_gate=AuthGate(required_roles=("custom_role",)),
        )
        ctrl.register_rule(rule)
        assert ctrl.get_rule("custom") is rule

    def test_get_screens_by_category(self):
        ctrl = AppStateController()
        admin_screens = ctrl.get_screens_by_category("administration")
        assert all(r.category == "administration" for r in admin_screens)

    def test_set_user_context_updates_access(self):
        ctrl = AppStateController()
        ctrl.system_state = AppSystemState.NORMAL
        ctrl.set_user_context(("admin",), True)
        assert ctrl.is_screen_available("settings") == ScreenAccess.GRANTED

    def test_inaccessible_screens(self):
        ctrl = AppStateController()
        ctrl.system_state = AppSystemState.SHUTDOWN
        inaccessible = ctrl.inaccessible_screens
        assert len(inaccessible) > 0

    def test_reset(self):
        ctrl = AppStateController()
        ctrl.system_state = AppSystemState.NORMAL
        ctrl.set_user_context(("admin",), True)
        ctrl.reset()
        assert ctrl.system_state == AppSystemState.STARTING
        assert ctrl._user_roles == ()

    @pytest.mark.parametrize("role,screen,expected", [
        ("admin", "user_management", ScreenAccess.GRANTED),
        ("admin", "settings", ScreenAccess.GRANTED),
        ("admin", "backup", ScreenAccess.GRANTED),
        ("editor", "letter_editor", ScreenAccess.GRANTED),
        ("viewer", "archive_browser", ScreenAccess.GRANTED),
        ("viewer", "search", ScreenAccess.GRANTED),
        ("viewer", "letter_editor", ScreenAccess.DENIED),
        ("editor", "user_management", ScreenAccess.DENIED),
        ("viewer", "settings", ScreenAccess.DENIED),
    ])
    def test_role_screen_matrix(self, role, screen, expected):
        ctrl = AppStateController()
        ctrl.system_state = AppSystemState.NORMAL
        ctrl.set_user_context((role,), True)
        assert ctrl.is_screen_available(screen) == expected
