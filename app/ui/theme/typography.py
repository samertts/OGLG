from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar


@dataclass(frozen=True)
class TypeScale:
    font_family: str = "Segoe UI"
    font_family_arabic: str = "Segoe UI"
    font_family_mono: str = "Consolas"
    font_family_arabic_mono: str = "IBM Plex Sans Arabic"

    scale_factor: float = 1.0

    display_large_size: int = 57
    display_large_weight: str = "300"
    display_medium_size: int = 45
    display_medium_weight: str = "400"
    display_small_size: int = 36
    display_small_weight: str = "400"

    headline_large_size: int = 32
    headline_large_weight: str = "400"
    headline_medium_size: int = 28
    headline_medium_weight: str = "400"
    headline_small_size: int = 24
    headline_small_weight: str = "500"

    title_large_size: int = 22
    title_large_weight: str = "400"
    title_medium_size: int = 16
    title_medium_weight: str = "500"
    title_small_size: int = 14
    title_small_weight: str = "500"

    body_large_size: int = 16
    body_large_weight: str = "400"
    body_medium_size: int = 14
    body_medium_weight: str = "400"
    body_small_size: int = 12
    body_small_weight: str = "400"

    label_large_size: int = 14
    label_large_weight: str = "500"
    label_medium_size: int = 12
    label_medium_weight: str = "500"
    label_small_size: int = 11
    label_small_weight: str = "500"

    button_size: int = 14
    button_weight: str = "500"
    button_letter_spacing: float = 0.5

    caption_size: int = 12
    caption_weight: str = "400"

    overline_size: int = 10
    overline_weight: str = "400"
    overline_letter_spacing: float = 1.5

    code_size: int = 13
    code_weight: str = "400"

    line_height_multiplier: float = 1.5
    paragraph_spacing: int = 8

    ARABIC_ADJUSTMENTS: ClassVar[dict[str, float]] = {
        "display_large_size": -4,
        "display_medium_size": -3,
        "display_small_size": -2,
        "headline_large_size": -2,
        "headline_medium_size": -2,
        "headline_small_size": -1,
        "title_large_size": -1,
        "body_large_size": 0,
        "body_medium_size": 0,
        "body_small_size": 0,
        "label_large_size": 0,
        "label_medium_size": 0,
        "label_small_size": 0,
        "button_size": 0,
        "caption_size": 0,
        "overline_size": 0,
        "code_size": 0,
    }
