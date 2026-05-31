from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SearchFilterState:
    query: str = ""
    sender: str = ""
    recipient: str = ""
    archive_type: str = ""
    date_from: str = ""
    date_to: str = ""
    arabic_normalize: bool = True

    def is_active(self) -> bool:
        return bool(
            self.query or self.sender or self.recipient
            or self.archive_type or self.date_from or self.date_to
        )

    def clear(self) -> None:
        self.query = ""
        self.sender = ""
        self.recipient = ""
        self.archive_type = ""
        self.date_from = ""
        self.date_to = ""


@dataclass
class SearchPaginationState:
    page: int = 0
    page_size: int = 20
    total_results: int = 0
    total_pages: int = 0

    @property
    def offset(self) -> int:
        return self.page * self.page_size

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

    def reset(self) -> None:
        self.page = 0
        self.total_results = 0
        self.total_pages = 0

    def update_from_count(self, total: int) -> None:
        self.total_results = total
        self.total_pages = max(1, (total + self.page_size - 1) // self.page_size)
        if self.page >= self.total_pages:
            self.page = self.total_pages - 1


@dataclass
class SearchResultItem:
    row_id: int
    snapshot_id: str
    archive_type: str
    source_id: str
    snippet: str
    score: float = 0.0
    created_at: str = ""


@dataclass
class SearchSessionState:
    filters: SearchFilterState = field(default_factory=SearchFilterState)
    pagination: SearchPaginationState = field(default_factory=SearchPaginationState)
    results: list[SearchResultItem] = field(default_factory=list)
    searching: bool = False
    error: str | None = None
    last_query_id: int = 0

    def set_results(self, items: list[SearchResultItem], total: int) -> None:
        self.results = items
        self.pagination.update_from_count(total)
        self.searching = False
        self.error = None
        self.last_query_id += 1

    def clear(self) -> None:
        self.results.clear()
        self.pagination.reset()
        self.searching = False
        self.error = None
