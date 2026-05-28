from __future__ import annotations

from pathlib import Path

from loguru import logger

from app.ui.theme.colors import ColorPalette, ColorScheme
from app.ui.theme.font_manager import FontManager
from app.ui.theme.icon_strategy import IconStrategy
from app.ui.theme.spacing import Spacing
from app.ui.theme.typography import TypeScale

try:
    from PySide6.QtCore import QLocale, Qt
    from PySide6.QtGui import QFont
    from PySide6.QtWidgets import QApplication, QProxyStyle, QStyle, QStyleFactory
except ImportError:
    QProxyStyle, QApplication = None, None


class RTLProxyStyle(QProxyStyle):
    def __init__(self, base_style: str | None = None) -> None:
        super().__init__(base_style or "Fusion")
        self._rtl = False

    def set_rtl(self, enabled: bool) -> None:
        self._rtl = enabled

    def drawPrimitive(
        self,
        element: QStyle.PrimitiveElement,
        option,
        painter,
        widget=None,
    ) -> None:
        if self._rtl and element in (
            QStyle.PE_IndicatorArrowLeft,
            QStyle.PE_IndicatorArrowRight,
        ):
            element = (
                QStyle.PE_IndicatorArrowRight
                if element == QStyle.PE_IndicatorArrowLeft
                else QStyle.PE_IndicatorArrowLeft
            )
        super().drawPrimitive(element, option, painter, widget)

    def subElementRect(
        self,
        element: QStyle.SubElement,
        option,
        widget=None,
    ) -> int:
        if self._rtl and element == QStyle.SE_CheckBoxIndicator:
            rect = super().subElementRect(element, option, widget)
            return rect
        return super().subElementRect(element, option, widget)

    def styleHint(
        self,
        hint: QStyle.StyleHint,
        option=None,
        widget=None,
        returnData=None,
    ) -> int:
        if self._rtl and hint == QStyle.SH_UnderlineShortcut:
            return 0
        return super().styleHint(hint, option, widget, returnData)


class ThemeManager:
    _instance: ThemeManager | None = None

    def __init__(self, app: QApplication | None = None) -> None:
        self._app = app
        self._scheme = ColorScheme.LIGHT
        self._palette = ColorPalette.for_scheme(ColorScheme.LIGHT)
        self._type_scale = TypeScale()
        self._spacing = Spacing()
        self._font_manager = FontManager.get_instance()
        self._icon_strategy = IconStrategy.get_instance()
        self._proxy_style: RTLProxyStyle | None = None
        self._rtl_enabled = False
        self._dpi_scale = 1.0
        self._initialized = False

    @classmethod
    def get_instance(cls) -> ThemeManager:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @property
    def palette(self) -> ColorPalette:
        return self._palette

    @property
    def colors(self) -> ColorPalette:
        return self._palette

    @property
    def typography(self) -> TypeScale:
        return self._type_scale

    @property
    def spacing(self) -> Spacing:
        return self._spacing

    @property
    def fonts(self) -> FontManager:
        return self._font_manager

    @property
    def icons(self) -> IconStrategy:
        return self._icon_strategy

    @property
    def dpi_scale(self) -> float:
        return self._dpi_scale

    @property
    def is_rtl(self) -> bool:
        return self._rtl_enabled

    @property
    def scheme(self) -> ColorScheme:
        return self._scheme

    def initialize(
        self,
        app: QApplication,
        font_dir: Path | None = None,
        rtl: bool = False,
        scheme: ColorScheme = ColorScheme.LIGHT,
    ) -> None:
        if self._initialized:
            return
        self._app = app
        self._scheme = scheme
        self._palette = ColorPalette.for_scheme(scheme)
        self._rtl_enabled = rtl
        self._detect_dpi_scale()
        self._setup_proxy_style()
        self._font_manager.register_arabic_fonts(font_dir)
        self._apply_application_palette()
        self._initialized = True
        logger.info(
            "Theme initialized",
            extra={
                "scheme": scheme.name,
                "rtl": rtl,
                "dpi_scale": self._dpi_scale,
            },
        )

    def set_color_scheme(self, scheme: ColorScheme) -> None:
        if scheme == self._scheme:
            return
        self._scheme = scheme
        self._palette = ColorPalette.for_scheme(scheme)
        self._apply_application_palette()
        logger.info("Color scheme changed", extra={"scheme": scheme.name})

    def set_rtl(self, enabled: bool) -> None:
        if enabled == self._rtl_enabled:
            return
        self._rtl_enabled = enabled
        if self._proxy_style:
            self._proxy_style.set_rtl(enabled)
        if self._app:
            layout = Qt.RightToLeft if enabled else Qt.LeftToRight
            self._app.setLayoutDirection(layout)
        logger.info("RTL mode changed", extra={"enabled": enabled})

    def detect_rtl_from_locale(self) -> bool:
        locale = QLocale()
        return locale.textDirection() == Qt.RightToLeft

    def set_dpi_scale(self, scale: float) -> None:
        self._dpi_scale = scale
        self._spacing = Spacing().scale(scale)
        logger.debug("DPI scale updated", extra={"scale": scale})

    def _detect_dpi_scale(self) -> None:
        if self._app is None:
            return
        screen = self._app.primaryScreen()
        if screen is None:
            return
        logical_dpi = screen.logicalDotsPerInch()
        base_dpi = 96.0
        self._dpi_scale = max(1.0, logical_dpi / base_dpi)
        self._spacing = Spacing().scale(self._dpi_scale)

    def _setup_proxy_style(self) -> None:
        if QProxyStyle is None or self._app is None:
            return
        base = QStyleFactory.create("Fusion")
        if base is None:
            return
        self._proxy_style = RTLProxyStyle()
        self._proxy_style.setBaseStyle(base)
        self._proxy_style.set_rtl(self._rtl_enabled)
        old_style = self._app.style()
        self._app.setStyle(self._proxy_style)
        if old_style:
            old_style.deleteLater()

    def _apply_application_palette(self) -> None:
        if self._app is None:
            return
        from PySide6.QtGui import QColor, QPalette

        p = QPalette()
        c = self._palette
        p.setColor(QPalette.Window, QColor(c.background))
        p.setColor(QPalette.WindowText, QColor(c.text_primary))
        p.setColor(QPalette.Base, QColor(c.surface))
        p.setColor(QPalette.AlternateBase, QColor(c.surface_variant))
        p.setColor(QPalette.ToolTipBase, QColor(c.surface))
        p.setColor(QPalette.ToolTipText, QColor(c.text_primary))
        p.setColor(QPalette.Text, QColor(c.text_primary))
        p.setColor(QPalette.Button, QColor(c.surface))
        p.setColor(QPalette.ButtonText, QColor(c.text_primary))
        p.setColor(QPalette.BrightText, QColor(c.error))
        p.setColor(QPalette.Link, QColor(c.link))
        p.setColor(QPalette.LinkVisited, QColor(c.link_visited))
        p.setColor(QPalette.Highlight, QColor(c.selected_bg))
        p.setColor(QPalette.HighlightedText, QColor(c.selected_fg))
        p.setColor(QPalette.Disabled, QPalette.WindowText, QColor(c.text_disabled))
        p.setColor(QPalette.Disabled, QPalette.Text, QColor(c.text_disabled))
        p.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(c.text_disabled))
        self._app.setPalette(p)

    def get_stylesheet(self) -> str:
        c = self._palette
        s = self._spacing
        return f"""
            QMainWindow {{
                background-color: {c.background};
            }}
            QWidget {{
                color: {c.text_primary};
                font-family: "{self._type_scale.font_family}";
            }}
            QPushButton {{
                background-color: {c.primary};
                color: {c.on_primary};
                border: none;
                border-radius: {s.border_radius_medium}px;
                padding: {s.padding_medium}px {s.padding_large}px;
                font-size: {self._type_scale.button_size}px;
                font-weight: {self._type_scale.button_weight};
                min-height: 32px;
            }}
            QPushButton:hover {{
                background-color: {c.primary_light};
            }}
            QPushButton:pressed {{
                background-color: {c.primary_dark};
            }}
            QPushButton:disabled {{
                background-color: {c.disabled_bg};
                color: {c.disabled_fg};
            }}
            QLineEdit, QTextEdit, QPlainTextEdit {{
                border: 1px solid {c.border};
                border-radius: {s.border_radius_medium}px;
                padding: {s.padding_small}px {s.padding_medium}px;
                background-color: {c.surface};
                selection-background-color: {c.selected_bg};
                selection-color: {c.selected_fg};
            }}
            QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
                border-color: {c.primary};
            }}
            QComboBox {{
                border: 1px solid {c.border};
                border-radius: {s.border_radius_medium}px;
                padding: {s.padding_small}px {s.padding_medium}px;
                background-color: {c.surface};
                min-height: 32px;
            }}
            QComboBox:focus {{
                border-color: {c.primary};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 24px;
            }}
            QCheckBox, QRadioButton {{
                spacing: {s.gap_small}px;
            }}
            QLabel {{
                color: {c.text_primary};
            }}
            QGroupBox {{
                border: 1px solid {c.border};
                border-radius: {s.border_radius_large}px;
                margin-top: 16px;
                padding-top: 16px;
                font-weight: bold;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 4px;
            }}
            QTableWidget, QTableView {{
                border: 1px solid {c.border};
                border-radius: {s.border_radius_medium}px;
                gridline-color: {c.divider};
                selection-background-color: {c.selected_bg};
                selection-color: {c.selected_fg};
                alternate-background-color: {c.table_stripe};
            }}
            QTableWidget::item, QTableView::item {{
                padding: {s.table_padding}px;
            }}
            QHeaderView::section {{
                background-color: {c.table_header_bg};
                color: {c.table_header_fg};
                padding: {s.padding_medium}px;
                border: none;
                border-bottom: 1px solid {c.border};
                font-weight: bold;
            }}
            QScrollBar:vertical {{
                background: {c.scrollbar_bg};
                width: 10px;
                border-radius: 5px;
            }}
            QScrollBar::handle:vertical {{
                background: {c.scrollbar_fg};
                min-height: 30px;
                border-radius: 5px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {c.scrollbar_hover};
            }}
            QScrollBar:horizontal {{
                background: {c.scrollbar_bg};
                height: 10px;
                border-radius: 5px;
            }}
            QScrollBar::handle:horizontal {{
                background: {c.scrollbar_fg};
                min-width: 30px;
                border-radius: 5px;
            }}
            QScrollBar::handle:horizontal:hover {{
                background: {c.scrollbar_hover};
            }}
            QScrollBar::add-line, QScrollBar::sub-line {{
                height: 0;
                width: 0;
            }}
            QScrollBar::add-page, QScrollBar::sub-page {{
                background: none;
            }}
            QMenuBar {{
                background-color: {c.surface};
                border-bottom: 1px solid {c.border};
            }}
            QMenuBar::item:selected {{
                background-color: {c.selected_bg};
            }}
            QMenu {{
                background-color: {c.surface};
                border: 1px solid {c.border};
                border-radius: {s.border_radius_medium}px;
                padding: {s.padding_small}px;
            }}
            QMenu::item:selected {{
                background-color: {c.selected_bg};
                color: {c.selected_fg};
            }}
            QTabWidget::pane {{
                border: 1px solid {c.border};
                border-radius: {s.border_radius_medium}px;
            }}
            QTabBar::tab {{
                padding: {s.padding_medium}px {s.padding_large}px;
                border: none;
                border-bottom: 2px solid transparent;
            }}
            QTabBar::tab:selected {{
                border-bottom: 2px solid {c.primary};
                color: {c.primary};
            }}
            QTabBar::tab:hover {{
                background-color: {c.surface_variant};
            }}
            QStatusBar {{
                background-color: {c.status_bar_bg};
                color: {c.status_bar_fg};
                border-top: 1px solid {c.border};
                font-size: {self._type_scale.body_small_size}px;
            }}
            QProgressBar {{
                border: none;
                border-radius: {s.border_radius_small}px;
                background-color: {c.surface_variant};
                height: 6px;
                text-align: center;
            }}
            QProgressBar::chunk {{
                background-color: {c.primary};
                border-radius: {s.border_radius_small}px;
            }}
            QToolTip {{
                background-color: {c.surface};
                color: {c.text_primary};
                border: 1px solid {c.border};
                border-radius: {s.border_radius_small}px;
                padding: {s.padding_small}px;
            }}
            QSplitter::handle {{
                background-color: {c.border};
                width: 1px;
            }}
        """
