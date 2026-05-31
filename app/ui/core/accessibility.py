from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any


class AccessibilityRole(Enum):
    BUTTON = auto()
    DIALOG = auto()
    PANEL = auto()
    FORM = auto()
    TABLE = auto()
    TREE = auto()
    NAVIGATION = auto()
    ALERT = auto()
    TOOLTIP = auto()
    STATUS_BAR = auto()
    TAB_PANEL = auto()
    SEARCH_BOX = auto()
    DOCUMENT = auto()
    LIST = auto()
    LIST_ITEM = auto()


@dataclass
class AccessibilityMetadata:
    role: AccessibilityRole = AccessibilityRole.PANEL
    label: str = ""
    description: str = ""
    keyboard_shortcut: str = ""
    tab_index: int = -1
    focusable: bool = True
    hidden_from_screen_reader: bool = False
    live_region: str = "off"
    aria_attributes: dict[str, str] = field(default_factory=dict)

    @property
    def is_interactive(self) -> bool:
        return self.role in (
            AccessibilityRole.BUTTON,
            AccessibilityRole.FORM,
            AccessibilityRole.SEARCH_BOX,
        )


@dataclass
class AccessibilityRegion:
    region_id: str
    label: str = ""
    role: str = "region"
    children: list[AccessibilityMetadata] = field(default_factory=list)
    expanded: bool = True
    description: str = ""

    def add_child(self, child: AccessibilityMetadata) -> None:
        self.children.append(child)


class AccessibilityService:
    MAX_REGIONS = 50

    def __init__(self) -> None:
        self._regions: dict[str, AccessibilityRegion] = {}
        self._focus_history: list[str] = []
        self._max_focus_history = 20

    def register_region(self, region: AccessibilityRegion) -> None:
        if len(self._regions) >= self.MAX_REGIONS:
            self._regions.pop(next(iter(self._regions)), None)
        self._regions[region.region_id] = region

    def get_region(self, region_id: str) -> AccessibilityRegion | None:
        return self._regions.get(region_id)

    @property
    def regions(self) -> list[AccessibilityRegion]:
        return list(self._regions.values())

    def record_focus(self, element_id: str) -> None:
        self._focus_history.append(element_id)
        if len(self._focus_history) > self._max_focus_history:
            self._focus_history.pop(0)

    @property
    def last_focused(self) -> str | None:
        return self._focus_history[-1] if self._focus_history else None

    def announce(self, message: str, priority: str = "polite") -> str:
        alert_id = f"announce_{hash(message) & 0xFFFF}"
        return alert_id

    def screen_reader_metadata(
        self, role: AccessibilityRole, label: str, **kwargs: Any,
    ) -> AccessibilityMetadata:
        return AccessibilityMetadata(role=role, label=label, **kwargs)

    def clear(self) -> None:
        self._regions.clear()
        self._focus_history.clear()
