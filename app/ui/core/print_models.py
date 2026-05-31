from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from typing import Any


class PageOrientation(Enum):
    PORTRAIT = auto()
    LANDSCAPE = auto()


@dataclass
class PageLayout:
    width_mm: float = 210.0
    height_mm: float = 297.0
    margin_top_mm: float = 25.0
    margin_bottom_mm: float = 25.0
    margin_left_mm: float = 25.0
    margin_right_mm: float = 25.0
    orientation: PageOrientation = PageOrientation.PORTRAIT

    @property
    def content_width_mm(self) -> float:
        return self.width_mm - self.margin_left_mm - self.margin_right_mm

    @property
    def content_height_mm(self) -> float:
        return self.height_mm - self.margin_top_mm - self.margin_bottom_mm

    def as_a4(self) -> None:
        self.width_mm = 210.0
        self.height_mm = 297.0
        self.orientation = PageOrientation.PORTRAIT

    def as_a4_landscape(self) -> None:
        self.width_mm = 297.0
        self.height_mm = 210.0
        self.orientation = PageOrientation.LANDSCAPE


@dataclass
class FooterMetadata:
    organization: str = ""
    document_id: str = ""
    page_number: int = 0
    total_pages: int = 0
    printed_at: str = ""
    audit_token: str | None = None
    classification: str = "unclassified"

    def render_lines(self) -> list[str]:
        lines: list[str] = []
        if self.organization:
            lines.append(self.organization)
        if self.document_id:
            lines.append(f"Doc: {self.document_id}")
        if self.total_pages > 0:
            lines.append(f"Page {self.page_number} of {self.total_pages}")
        if self.printed_at:
            lines.append(self.printed_at)
        if self.classification and self.classification != "unclassified":
            lines.append(f"[{self.classification.upper()}]")
        return lines


@dataclass
class PageNumbering:
    start_page: int = 1
    format_str: str = "Page {page} of {total}"
    show_on_first_page: bool = True

    def format(self, page: int, total: int) -> str:
        return self.format_str.format(page=page + self.start_page - 1, total=total)


@dataclass
class DocumentTemplate:
    template_id: str = "default"
    name: str = "Standard Government Document"
    layout: PageLayout = field(default_factory=PageLayout)
    footer: FooterMetadata = field(default_factory=FooterMetadata)
    rtl: bool = True
    font_size_body: float = 11.0
    font_size_header: float = 14.0
    line_spacing: float = 1.5
    show_border: bool = True
    show_header: bool = True
    show_footer: bool = True
    page_numbering: PageNumbering = field(default_factory=PageNumbering)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class DocumentSection:
    title: str = ""
    content: str = ""
    is_rtl: bool = True
    font_size: float | None = None
    bold: bool = False
    page_break_before: bool = False


@dataclass
class PrintDocument:
    document_id: str
    title: str = ""
    template: DocumentTemplate = field(default_factory=DocumentTemplate)
    sections: list[DocumentSection] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    audit_token: str | None = None

    def add_section(self, title: str, content: str, **kwargs: Any) -> DocumentSection:
        section = DocumentSection(title=title, content=content, **kwargs)
        self.sections.append(section)
        return section

    @property
    def total_sections(self) -> int:
        return len(self.sections)

    @property
    def estimated_pages(self) -> int:
        char_count = sum(len(s.content) for s in self.sections)
        return max(1, (char_count + 3000) // 3000)
