import os

os.environ["QT_QPA_PLATFORM"] = "offscreen"

try:
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QFont
    from PySide6.QtWidgets import QApplication
except ImportError:
    pass


from app.ui.theme.colors import ColorPalette, ColorScheme
from app.ui.theme.spacing import Spacing
from app.ui.theme.typography import TypeScale


class TestColorPalette:
    def test_light_scheme_defaults(self):
        palette = ColorPalette()
        assert palette.primary == "#1B5E20"
        assert palette.background == "#FAFAFA"

    def test_dark_scheme(self):
        palette = ColorPalette.for_scheme(ColorScheme.DARK)
        assert palette.primary == ColorPalette.DARK_PRIMARY
        assert palette.background == "#121212"

    def test_high_contrast_scheme(self):
        palette = ColorPalette.for_scheme(ColorScheme.HIGH_CONTRAST)
        assert palette.primary == "#000000"
        assert palette.background == "#FFFFFF"

    def test_as_dict(self):
        palette = ColorPalette()
        d = palette.as_dict()
        assert isinstance(d, dict)
        assert d["primary"] == "#1B5E20"
        assert d["background"] == "#FAFAFA"


class TestSpacing:
    def test_default_values(self):
        s = Spacing()
        assert s.unit == 4
        assert s.sidebar_width == 240
        assert s.default_window_width == 1280

    def test_scale(self):
        s = Spacing()
        scaled = s.scale(2.0)
        assert scaled.sidebar_width == 480
        assert scaled.unit == 8
        assert scaled.min_window_width == 1600

    def test_scale_minimum_one(self):
        s = Spacing()
        scaled = s.scale(0.1)
        assert scaled.unit >= 1
        assert scaled.xs >= 1


class TestTypeScale:
    def test_default_values(self):
        t = TypeScale()
        assert t.body_medium_size == 14
        assert t.body_medium_weight == "400"
        assert t.font_family == "Segoe UI"

    def test_arabic_adjustments_keys(self):
        assert "display_large_size" in TypeScale.ARABIC_ADJUSTMENTS
        assert "button_size" in TypeScale.ARABIC_ADJUSTMENTS
