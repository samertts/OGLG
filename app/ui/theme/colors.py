from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import ClassVar


class ColorScheme(Enum):
    LIGHT = auto()
    DARK = auto()
    HIGH_CONTRAST = auto()


@dataclass(frozen=True)
class ColorPalette:
    primary: str = "#1B5E20"
    primary_light: str = "#4C8C4A"
    primary_dark: str = "#003300"
    secondary: str = "#F57F17"
    secondary_light: str = "#FFB04C"
    secondary_dark: str = "#BC5100"
    accent: str = "#1565C0"
    accent_light: str = "#5E92F3"
    accent_dark: str = "#003C8F"
    background: str = "#FAFAFA"
    surface: str = "#FFFFFF"
    surface_variant: str = "#F5F5F5"
    error: str = "#D32F2F"
    error_light: str = "#EF5350"
    error_dark: str = "#C62828"
    success: str = "#2E7D32"
    success_light: str = "#4CAF50"
    warning: str = "#F57F17"
    warning_light: str = "#FFB300"
    info: str = "#1565C0"
    info_light: str = "#42A5F5"
    on_primary: str = "#FFFFFF"
    on_secondary: str = "#000000"
    on_background: str = "#212121"
    on_surface: str = "#212121"
    on_error: str = "#FFFFFF"
    text_primary: str = "#212121"
    text_secondary: str = "#757575"
    text_disabled: str = "#BDBDBD"
    border: str = "#E0E0E0"
    border_light: str = "#F0F0F0"
    divider: str = "#EEEEEE"
    shadow: str = "#0000001A"
    overlay: str = "#00000040"
    disabled_bg: str = "#E0E0E0"
    disabled_fg: str = "#9E9E9E"
    link: str = "#1565C0"
    link_visited: str = "#7B1FA2"
    highlight: str = "#FFF9C4"
    selected_bg: str = "#E3F2FD"
    selected_fg: str = "#1565C0"
    sidebar_bg: str = "#1B5E20"
    sidebar_fg: str = "#FFFFFF"
    sidebar_hover: str = "#4C8C4A"
    sidebar_selected: str = "#F57F17"
    header_bg: str = "#FFFFFF"
    header_fg: str = "#212121"
    header_border: str = "#E0E0E0"
    status_bar_bg: str = "#F5F5F5"
    status_bar_fg: str = "#616161"
    toast_info_bg: str = "#E3F2FD"
    toast_info_fg: str = "#1565C0"
    toast_success_bg: str = "#E8F5E9"
    toast_success_fg: str = "#2E7D32"
    toast_warning_bg: str = "#FFF3E0"
    toast_warning_fg: str = "#E65100"
    toast_error_bg: str = "#FFEBEE"
    toast_error_fg: str = "#C62828"
    scrollbar_bg: str = "#F5F5F5"
    scrollbar_fg: str = "#BDBDBD"
    scrollbar_hover: str = "#9E9E9E"
    table_stripe: str = "#F9F9F9"
    table_header_bg: str = "#F5F5F5"
    table_header_fg: str = "#616161"
    focus_ring: str = "#1565C080"
    dialog_bg: str = "#FFFFFF"
    dialog_title_bg: str = "#1B5E20"
    dialog_title_fg: str = "#FFFFFF"
    dialog_overlay: str = "#00000066"
    busy_overlay: str = "#FFFFFFCC"
    busy_spinner: str = "#1B5E20"
    splash_bg: str = "#FFFFFF"
    splash_fg: str = "#1B5E20"
    splash_accent: str = "#F57F17"

    DARK_PRIMARY: ClassVar[str] = "#66BB6A"
    DARK_PRIMARY_LIGHT: ClassVar[str] = "#98EE99"
    DARK_PRIMARY_DARK: ClassVar[str] = "#338A3E"
    DARK_BACKGROUND: ClassVar[str] = "#121212"
    DARK_SURFACE: ClassVar[str] = "#1E1E1E"
    DARK_SURFACE_VARIANT: ClassVar[str] = "#2C2C2C"
    DARK_ON_BACKGROUND: ClassVar[str] = "#E0E0E0"
    DARK_ON_SURFACE: ClassVar[str] = "#E0E0E0"
    DARK_TEXT_PRIMARY: ClassVar[str] = "#E0E0E0"
    DARK_TEXT_SECONDARY: ClassVar[str] = "#9E9E9E"
    DARK_BORDER: ClassVar[str] = "#383838"
    DARK_SIDEBAR_BG: ClassVar[str] = "#1B5E20"
    DARK_SIDEBAR_HOVER: ClassVar[str] = "#2E7D32"

    def as_dict(self) -> dict[str, str]:
        return {
            k: v for k, v in self.__dict__.items() if isinstance(v, str) and not k.startswith("_")
        }

    @classmethod
    def for_scheme(cls, scheme: ColorScheme) -> ColorPalette:
        if scheme == ColorScheme.LIGHT:
            return cls()
        if scheme == ColorScheme.DARK:
            return cls(
                primary=cls.DARK_PRIMARY,
                primary_light=cls.DARK_PRIMARY_LIGHT,
                primary_dark=cls.DARK_PRIMARY_DARK,
                background=cls.DARK_BACKGROUND,
                surface=cls.DARK_SURFACE,
                surface_variant=cls.DARK_SURFACE_VARIANT,
                on_background=cls.DARK_ON_BACKGROUND,
                on_surface=cls.DARK_ON_SURFACE,
                text_primary=cls.DARK_TEXT_PRIMARY,
                text_secondary=cls.DARK_TEXT_SECONDARY,
                border=cls.DARK_BORDER,
                sidebar_bg=cls.DARK_SIDEBAR_BG,
                sidebar_hover=cls.DARK_SIDEBAR_HOVER,
                header_bg=cls.DARK_SURFACE,
                header_fg=cls.DARK_TEXT_PRIMARY,
                status_bar_bg=cls.DARK_SURFACE_VARIANT,
                status_bar_fg=cls.DARK_TEXT_SECONDARY,
                dialog_bg=cls.DARK_SURFACE,
                dialog_title_bg=cls.DARK_PRIMARY,
                splash_bg=cls.DARK_SURFACE,
                splash_fg=cls.DARK_PRIMARY,
                table_stripe=cls.DARK_SURFACE_VARIANT,
                table_header_bg=cls.DARK_SURFACE_VARIANT,
                divider=cls.DARK_BORDER,
                scrollbar_bg=cls.DARK_SURFACE_VARIANT,
                scrollbar_fg="#555555",
                scrollbar_hover="#777777",
                highlight=cls.DARK_SIDEBAR_HOVER,
                selected_bg=cls.DARK_PRIMARY_DARK,
                disabled_bg="#333333",
                disabled_fg="#666666",
                toast_info_bg="#1A237E",
                toast_success_bg="#1B5E20",
                toast_warning_bg="#E65100",
                toast_error_bg="#B71C1C",
                dialog_overlay="#00000080",
                busy_overlay="#00000099",
            )
        if scheme == ColorScheme.HIGH_CONTRAST:
            return cls(
                primary="#000000",
                primary_light="#333333",
                primary_dark="#000000",
                background="#FFFFFF",
                surface="#FFFFFF",
                error="#FF0000",
                on_primary="#FFFFFF",
                on_background="#000000",
                on_surface="#000000",
                text_primary="#000000",
                text_secondary="#000000",
                border="#000000",
                divider="#000000",
                sidebar_bg="#000000",
                sidebar_fg="#FFFFFF",
                sidebar_hover="#333333",
                sidebar_selected="#FFFFFF",
                focus_ring="#FF0000",
                link="#0000FF",
                splash_bg="#FFFFFF",
                splash_fg="#000000",
            )
        return cls()
