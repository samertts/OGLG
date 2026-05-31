"""Integration tests: auth context drives screen availability."""

from __future__ import annotations

import pytest

from app.ui.core.app_state_controller import AppStateController, AppSystemState, ScreenAccess


class TestAuthScreenIntegration:
    def test_admin_sees_all_administration_screens(self, ui_app_state: AppStateController):
        ui_app_state.set_user_context(("admin",), True)
        assert ui_app_state.is_screen_available("user_management") == ScreenAccess.GRANTED
        assert ui_app_state.is_screen_available("settings") == ScreenAccess.GRANTED
        assert ui_app_state.is_screen_available("backup") == ScreenAccess.GRANTED
        assert ui_app_state.is_screen_available("diagnostics") == ScreenAccess.GRANTED

    def test_viewer_sees_records_but_not_admin(self, ui_app_state: AppStateController):
        ui_app_state.set_user_context(("viewer",), True)
        assert ui_app_state.is_screen_available("dashboard") == ScreenAccess.GRANTED
        assert ui_app_state.is_screen_available("archive_browser") == ScreenAccess.GRANTED
        assert ui_app_state.is_screen_available("search") == ScreenAccess.GRANTED
        assert ui_app_state.is_screen_available("user_management") == ScreenAccess.DENIED
        assert ui_app_state.is_screen_available("letter_editor") == ScreenAccess.DENIED

    def test_editor_sees_correspondence_screens(self, ui_app_state: AppStateController):
        ui_app_state.set_user_context(("editor",), True)
        assert ui_app_state.is_screen_available("letter_editor") == ScreenAccess.GRANTED
        assert ui_app_state.is_screen_available("dashboard") == ScreenAccess.GRANTED
        assert ui_app_state.is_screen_available("about") == ScreenAccess.GRANTED

    def test_approver_has_both_editor_and_viewer_access(self, ui_app_state: AppStateController):
        ui_app_state.set_user_context(("approver",), True)
        assert ui_app_state.is_screen_available("letter_editor") == ScreenAccess.GRANTED
        assert ui_app_state.is_screen_available("archive_browser") == ScreenAccess.GRANTED
        assert ui_app_state.is_screen_available("search") == ScreenAccess.GRANTED

    def test_inactive_user_denied_all_gated_screens(self, ui_app_state: AppStateController):
        ui_app_state.set_user_context(("admin",), active=False)
        assert ui_app_state.is_screen_available("dashboard") == ScreenAccess.GRANTED
        assert ui_app_state.is_screen_available("user_management") == ScreenAccess.DENIED
        assert ui_app_state.is_screen_available("settings") == ScreenAccess.DENIED

    def test_system_state_gating(self, ui_app_state: AppStateController):
        ui_app_state.set_user_context(("admin",), True)
        ui_app_state.system_state = AppSystemState.RECOVERY
        assert ui_app_state.is_screen_available("backup") == ScreenAccess.GRANTED
        assert ui_app_state.is_screen_available("diagnostics") == ScreenAccess.DENIED

    def test_shutdown_blocks_all_screens(self, ui_app_state: AppStateController):
        ui_app_state.system_state = AppSystemState.SHUTDOWN
        for sid in list(ui_app_state._rules.keys()):
            assert ui_app_state.is_screen_available(sid) == ScreenAccess.DENIED, f"{sid} not denied"

    def test_available_screens_respects_role(self, ui_app_state: AppStateController):
        ui_app_state.set_user_context(("viewer",), True)
        ids = {s.screen_id for s in ui_app_state.available_screens}
        assert "dashboard" in ids
        assert "user_management" not in ids
        assert "letter_editor" not in ids

    def test_role_transition_updates_availability(self, ui_app_state: AppStateController):
        ui_app_state.set_user_context(("viewer",), True)
        assert ui_app_state.is_screen_available("letter_editor") == ScreenAccess.DENIED
        ui_app_state.set_user_context(("editor", "viewer"), True)
        assert ui_app_state.is_screen_available("letter_editor") == ScreenAccess.GRANTED

    @pytest.mark.parametrize("roles,screen,expected", [
        (("admin",), "user_management", ScreenAccess.GRANTED),
        (("admin",), "about", ScreenAccess.GRANTED),
        (("editor", "admin"), "user_management", ScreenAccess.GRANTED),
        (("editor", "admin"), "letter_editor", ScreenAccess.GRANTED),
        (("viewer",), "dashboard", ScreenAccess.GRANTED),
        (("viewer",), "about", ScreenAccess.GRANTED),
        (("viewer",), "settings", ScreenAccess.DENIED),
    ])
    def test_role_combinations(self, ui_app_state, roles, screen, expected):
        ui_app_state.set_user_context(roles, True)
        assert ui_app_state.is_screen_available(screen) == expected
