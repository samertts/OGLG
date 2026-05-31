from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class RtlAlignment(Enum):
    LEFT = "left"
    RIGHT = "right"
    CENTER = "center"
    JUSTIFY = "justify"
    AUTO = "auto"


@dataclass
class RtlContract:
    enabled: bool = True
    alignment: RtlAlignment = RtlAlignment.RIGHT
    mirror_layout: bool = True
    arabic_font_scale: float = 1.05
    line_height_scale: float = 1.6
    supported_locales: tuple[str, ...] = ("ar", "ar_SA", "ar_IQ", "ar_EG")

    def is_rtl_locale(self, locale: str) -> bool:
        return locale in self.supported_locales or locale.startswith("ar")

    def _has_arabic(self, text: str) -> bool:
        return any(
            "\u0600" <= c <= "\u06FF" or "\u0750" <= c <= "\u077F"
            or "\u08A0" <= c <= "\u08FF" or "\uFB50" <= c <= "\uFDFF"
            or "\uFE70" <= c <= "\uFEFF" for c in text
        )

    def apply_text_direction(self, text: str) -> dict[str, str]:
        return {"text": text, "direction": "rtl" if self._has_arabic(text) else "ltr"}

    def sanitize_html_rtl(self, html: str) -> str:
        dir_attr = 'dir="rtl"' if self.enabled else 'dir="ltr"'
        if html.startswith("<"):
            return html.replace("<html", f'<html {dir_attr}', 1) if "<html" in html else html
        return html
