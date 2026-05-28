import os

os.environ["QT_QPA_PLATFORM"] = "offscreen"

import pytest

from app.ui.navigation.screen_router import ScreenEntry, ScreenRegistry, ScreenRouter


@pytest.fixture
def fake_screen_entry():
    class FakeVM:
        def __init__(self):
            self.screen_id = "test"
            self.title = "Test Screen"
            self.state = "IDLE"

        def initialize(self):
            self.state = "READY"

        def dispose(self):
            self.state = "DISPOSED"

    class FakeCtrl:
        def __init__(self):
            self.initialized = False

        def initialize(self):
            self.initialized = True

        def dispose(self):
            self.initialized = False

    class FakeWid:
        pass

    vm = FakeVM()
    ctrl = FakeCtrl()
    wid = FakeWid()
    entry = ScreenEntry(
        id="test",
        view_model=vm,
        controller=ctrl,
        widget=wid,
        title="Test Screen",
        icon_name="test",
        category="main",
        order=0,
    )
    return entry, vm, ctrl, wid


@pytest.fixture
def registry_with_screens(fake_screen_entry):
    entry, _, _, _ = fake_screen_entry

    class FakeVM2:
        def __init__(self):
            self.screen_id = "test2"
            self.title = "Test Screen 2"
            self.state = "IDLE"

        def initialize(self):
            self.state = "READY"

        def dispose(self):
            self.state = "DISPOSED"

    class FakeCtrl2:
        def __init__(self):
            self.initialized = False

        def initialize(self):
            self.initialized = True

        def dispose(self):
            self.initialized = False

    class FakeWid2:
        pass

    vm2 = FakeVM2()
    ctrl2 = FakeCtrl2()
    wid2 = FakeWid2()
    entry2 = ScreenEntry(
        id="test2",
        view_model=vm2,
        controller=ctrl2,
        widget=wid2,
        title="Test Screen 2",
        icon_name="test2",
        category="main",
        order=1,
    )

    reg = ScreenRegistry()
    reg.register(entry)
    reg.register(entry2)
    return reg, entry, entry2


class TestScreenRegistry:
    def test_register_and_get(self, fake_screen_entry):
        entry, _, _, _ = fake_screen_entry
        reg = ScreenRegistry()
        reg.register(entry)
        assert reg.get("test") is entry
        assert "test" in reg

    def test_duplicate_raises(self, fake_screen_entry):
        entry, _, _, _ = fake_screen_entry
        reg = ScreenRegistry()
        reg.register(entry)
        with pytest.raises(ValueError):
            reg.register(entry)

    def test_screens_sorted_by_order(self, fake_screen_entry):
        entry, _, _, _ = fake_screen_entry
        reg = ScreenRegistry()

        class FakeVM2:
            def __init__(self):
                self.screen_id = "second"
                self.title = "Second"
                self.state = "IDLE"

            def initialize(self):
                pass

            def dispose(self):
                pass

        class FakeCtrl2:
            def __init__(self):
                self.initialized = False

            def initialize(self):
                pass

            def dispose(self):
                pass

        class FakeWid2:
            pass

        entry1 = ScreenEntry(
            id="first",
            view_model=entry.view_model,
            controller=entry.controller,
            widget=entry.widget,
            title="First",
            order=5,
        )
        entry2 = ScreenEntry(
            id="second",
            view_model=FakeVM2(),
            controller=FakeCtrl2(),
            widget=FakeWid2(),
            title="Second",
            order=1,
        )
        reg.register(entry1)
        reg.register(entry2)
        screens = reg.screens
        assert screens[0].id == "second"
        assert screens[1].id == "first"


class TestScreenRouter:
    def test_initial_state(self, registry_with_screens):
        reg, _, _ = registry_with_screens
        router = ScreenRouter(reg)
        assert router.current_id is None
        assert router.current_screen is None

    def test_navigate_to(self, registry_with_screens):
        reg, entry, _ = registry_with_screens
        router = ScreenRouter(reg)
        result = router.navigate_to("test")
        assert result
        assert router.current_id == "test"

    def test_navigate_to_missing_screen(self, registry_with_screens):
        reg, _, _ = registry_with_screens
        router = ScreenRouter(reg)
        result = router.navigate_to("nonexistent")
        assert not result

    def test_navigate_back(self, registry_with_screens):
        reg, entry1, entry2 = registry_with_screens
        router = ScreenRouter(reg)
        router.navigate_to("test")
        router.navigate_to("test2")
        assert router.current_id == "test2"
        result = router.navigate_back()
        assert result
        assert router.current_id == "test"

    def test_navigate_back_empty_history(self, registry_with_screens):
        reg, _, _ = registry_with_screens
        router = ScreenRouter(reg)
        router.navigate_to("test")
        result = router.navigate_back()
        assert not result

    def test_navigate_home(self, registry_with_screens):
        reg, entry, entry2 = registry_with_screens
        router = ScreenRouter(reg)
        router.navigate_to("test2")
        result = router.navigate_home()
        assert result
        assert router.current_id == "test"

    def test_current_nav_path(self, registry_with_screens):
        reg, _, _ = registry_with_screens
        router = ScreenRouter(reg)
        router.navigate_to("test")
        router.navigate_to("test2")
        path = router.current_nav_path()
        assert path == ["test", "test2"]

    def test_shutdown_disposes_screens(self, registry_with_screens):
        reg, entry, entry2 = registry_with_screens
        router = ScreenRouter(reg)
        router.navigate_to("test")
        router.shutdown()
        assert not entry.controller.initialized
        assert not entry2.controller.initialized

    def test_double_navigation_same_screen(self, registry_with_screens):
        reg, _, _ = registry_with_screens
        router = ScreenRouter(reg)
        router.navigate_to("test")
        router.navigate_to("test")
        assert len(router.history) == 0

    def test_screen_changed_signal(self, registry_with_screens):
        reg, _, _ = registry_with_screens
        router = ScreenRouter(reg)
        signals = []
        router.screen_changed.connect(lambda sid: signals.append(sid))
        router.navigate_to("test")
        assert signals == ["test"]

    def test_navigation_failed_signal(self, registry_with_screens):
        reg, _, _ = registry_with_screens
        router = ScreenRouter(reg)
        signals = []
        router.navigation_failed.connect(lambda sid, reason: signals.append((sid, reason)))
        router.navigate_to("nonexistent")
        assert len(signals) == 1
        assert signals[0][0] == "nonexistent"
