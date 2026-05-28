from __future__ import annotations

try:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QApplication, QWidget
except ImportError:
    QWidget = object


class DPIScaling:
    BASE_DPI = 96.0

    _instance: DPIScaling | None = None

    def __init__(self) -> None:
        self._scale_factor = 1.0
        self._logical_dpi = self.BASE_DPI

    @classmethod
    def get_instance(cls) -> DPIScaling:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @property
    def scale_factor(self) -> float:
        return self._scale_factor

    @property
    def logical_dpi(self) -> float:
        return self._logical_dpi

    def detect(self, app: QApplication) -> None:
        screen = app.primaryScreen()
        if screen is None:
            return
        self._logical_dpi = screen.logicalDotsPerInch()
        self._scale_factor = max(1.0, self._logical_dpi / self.BASE_DPI)
        screen_factor = screen.devicePixelRatio()
        self._scale_factor = max(self._scale_factor, screen_factor)

    def scaled(self, value: int) -> int:
        return max(1, round(value * self._scale_factor))

    def scaled_font(self, base_size: int) -> int:
        return max(6, round(base_size * self._scale_factor))

    @staticmethod
    def set_high_dpi_attributes() -> None:
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
