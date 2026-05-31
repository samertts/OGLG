from __future__ import annotations

from app.ui.core.accessibility import (
    AccessibilityMetadata,
    AccessibilityRegion,
    AccessibilityRole,
    AccessibilityService,
)


class TestAccessibilityMetadata:
    def test_defaults(self):
        meta = AccessibilityMetadata()
        assert meta.role == AccessibilityRole.PANEL
        assert meta.focusable
        assert not meta.hidden_from_screen_reader

    def test_is_interactive(self):
        button = AccessibilityMetadata(role=AccessibilityRole.BUTTON)
        assert button.is_interactive
        panel = AccessibilityMetadata(role=AccessibilityRole.PANEL)
        assert not panel.is_interactive


class TestAccessibilityRegion:
    def test_add_child(self):
        region = AccessibilityRegion(region_id="main_nav", label="Main Navigation")
        child = AccessibilityMetadata(role=AccessibilityRole.BUTTON, label="Submit")
        region.add_child(child)
        assert len(region.children) == 1


class TestAccessibilityService:
    def test_register_and_get_region(self):
        svc = AccessibilityService()
        region = AccessibilityRegion(region_id="header", label="Header")
        svc.register_region(region)
        assert svc.get_region("header") is region

    def test_regions_list(self):
        svc = AccessibilityService()
        svc.register_region(AccessibilityRegion(region_id="r1"))
        svc.register_region(AccessibilityRegion(region_id="r2"))
        assert len(svc.regions) == 2

    def test_max_regions_prunes(self):
        svc = AccessibilityService()
        svc.MAX_REGIONS = 3
        for i in range(10):
            svc.register_region(AccessibilityRegion(region_id=f"r{i}"))
        assert len(svc.regions) <= 3

    def test_focus_history(self):
        svc = AccessibilityService()
        svc.record_focus("btn_save")
        svc.record_focus("btn_cancel")
        assert svc.last_focused == "btn_cancel"

    def test_max_focus_history(self):
        svc = AccessibilityService()
        for i in range(50):
            svc.record_focus(f"elem_{i}")
        assert len(svc._focus_history) <= 20

    def test_announce(self):
        svc = AccessibilityService()
        alert_id = svc.announce("Document saved", "polite")
        assert alert_id.startswith("announce_")

    def test_screen_reader_metadata(self):
        svc = AccessibilityService()
        meta = svc.screen_reader_metadata(AccessibilityRole.BUTTON, "Save")
        assert meta.role == AccessibilityRole.BUTTON
        assert meta.label == "Save"

    def test_clear(self):
        svc = AccessibilityService()
        svc.register_region(AccessibilityRegion(region_id="r1"))
        svc.record_focus("btn")
        svc.clear()
        assert len(svc.regions) == 0
        assert svc.last_focused is None
