from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ArchiveEntryPreview:
    entry_id: str
    snapshot_id: str
    archive_type: str
    source_id: str
    checksum: str
    created_at: str = ""
    preview_snippet: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ArchiveBrowseState:
    entries: list[ArchiveEntryPreview] = field(default_factory=list)
    filter_type: str = ""
    page: int = 0
    page_size: int = 50
    total_entries: int = 0
    loading: bool = False
    error: str | None = None

    @property
    def total_pages(self) -> int:
        return max(1, (self.total_entries + self.page_size - 1) // self.page_size)

    @property
    def has_next(self) -> bool:
        return self.page < self.total_pages - 1

    @property
    def has_previous(self) -> bool:
        return self.page > 0

    def next_page(self) -> None:
        if self.has_next:
            self.page += 1

    def previous_page(self) -> None:
        if self.has_previous:
            self.page -= 1

    def set_entries(self, items: list[ArchiveEntryPreview], total: int) -> None:
        self.entries = items
        self.total_entries = total
        self.loading = False
        self.error = None

    def clear(self) -> None:
        self.entries.clear()
        self.page = 0
        self.total_entries = 0
        self.loading = False
        self.error = None


@dataclass
class PreviewState:
    preview_type: str = ""  # "archive" | "attachment"
    item_id: str = ""
    title: str = ""
    content_preview: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    loading: bool = False
    error: str | None = None

    def set_preview(
        self, preview_type: str, item_id: str,
        title: str, content: str, **meta: Any,
    ) -> None:
        self.preview_type = preview_type
        self.item_id = item_id
        self.title = title
        self.content_preview = content
        self.metadata = meta
        self.loading = False
        self.error = None

    def clear(self) -> None:
        self.preview_type = ""
        self.item_id = ""
        self.title = ""
        self.content_preview = ""
        self.metadata.clear()
        self.loading = False
        self.error = None
