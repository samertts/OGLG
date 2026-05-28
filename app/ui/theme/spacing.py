from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Spacing:
    unit: int = 4

    xs: int = 4
    sm: int = 8
    md: int = 16
    lg: int = 24
    xl: int = 32
    xxl: int = 48
    xxxl: int = 64

    padding_tiny: int = 2
    padding_small: int = 4
    padding_medium: int = 8
    padding_large: int = 12
    padding_xlarge: int = 16

    margin_tiny: int = 2
    margin_small: int = 4
    margin_medium: int = 8
    margin_large: int = 12
    margin_xlarge: int = 16

    gap_tiny: int = 2
    gap_small: int = 4
    gap_medium: int = 8
    gap_large: int = 12
    gap_xlarge: int = 16

    border_radius_small: int = 2
    border_radius_medium: int = 4
    border_radius_large: int = 8
    border_radius_xlarge: int = 12
    border_radius_circle: int = 9999

    icon_size_small: int = 16
    icon_size_medium: int = 24
    icon_size_large: int = 32
    icon_size_xlarge: int = 48

    sidebar_width: int = 240
    sidebar_collapsed_width: int = 56
    sidebar_icon_size: int = 24
    sidebar_item_height: int = 48

    header_height: int = 56
    header_icon_size: int = 24
    header_logo_size: int = 32

    status_bar_height: int = 28
    status_bar_icon_size: int = 14

    min_window_width: int = 800
    min_window_height: int = 600
    default_window_width: int = 1280
    default_window_height: int = 800

    dialog_min_width: int = 400
    dialog_max_width: int = 600
    dialog_title_height: int = 48

    toast_width: int = 360
    toast_min_height: int = 48
    toast_margin: int = 16
    toast_spacing: int = 8

    splash_logo_size: int = 128
    splash_progress_height: int = 4
    splash_text_margin: int = 32

    table_row_height: int = 48
    table_header_height: int = 40
    table_padding: int = 12

    card_padding: int = 16
    card_border_radius: int = 8
    card_spacing: int = 16
    card_min_width: int = 280
    card_elevation: int = 2

    form_spacing: int = 16
    form_label_width: int = 120
    form_field_spacing: int = 8

    section_spacing: int = 24
    group_spacing: int = 16
    item_spacing: int = 8

    tab_icon_size: int = 20
    tab_height: int = 40
    tab_min_width: int = 80

    tooltip_delay: int = 500
    tooltip_duration: int = 5000
    animation_duration: int = 200
    transition_duration: int = 250
    debounce_delay: int = 300
    toast_duration: int = 3000
    busy_min_duration: int = 500
    status_clear_delay: int = 5000

    def scale(self, factor: float) -> Spacing:
        def s(v: int) -> int:
            return max(1, round(v * factor))

        return Spacing(
            unit=s(self.unit),
            xs=s(self.xs),
            sm=s(self.sm),
            md=s(self.md),
            lg=s(self.lg),
            xl=s(self.xl),
            xxl=s(self.xxl),
            xxxl=s(self.xxxl),
            padding_tiny=s(self.padding_tiny),
            padding_small=s(self.padding_small),
            padding_medium=s(self.padding_medium),
            padding_large=s(self.padding_large),
            padding_xlarge=s(self.padding_xlarge),
            margin_tiny=s(self.margin_tiny),
            margin_small=s(self.margin_small),
            margin_medium=s(self.margin_medium),
            margin_large=s(self.margin_large),
            margin_xlarge=s(self.margin_xlarge),
            gap_tiny=s(self.gap_tiny),
            gap_small=s(self.gap_small),
            gap_medium=s(self.gap_medium),
            gap_large=s(self.gap_large),
            gap_xlarge=s(self.gap_xlarge),
            border_radius_small=s(self.border_radius_small),
            border_radius_medium=s(self.border_radius_medium),
            border_radius_large=s(self.border_radius_large),
            border_radius_xlarge=s(self.border_radius_xlarge),
            border_radius_circle=s(self.border_radius_circle),
            icon_size_small=s(self.icon_size_small),
            icon_size_medium=s(self.icon_size_medium),
            icon_size_large=s(self.icon_size_large),
            icon_size_xlarge=s(self.icon_size_xlarge),
            sidebar_width=s(self.sidebar_width),
            sidebar_collapsed_width=s(self.sidebar_collapsed_width),
            header_height=s(self.header_height),
            status_bar_height=s(self.status_bar_height),
            min_window_width=s(self.min_window_width),
            min_window_height=s(self.min_window_height),
            dialog_min_width=s(self.dialog_min_width),
            toast_width=s(self.toast_width),
            splash_logo_size=s(self.splash_logo_size),
            table_row_height=s(self.table_row_height),
            card_padding=s(self.card_padding),
            card_min_width=s(self.card_min_width),
            form_label_width=s(self.form_label_width),
            tab_height=s(self.tab_height),
        )
