from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class MemoryScope(Enum):
    WIDGET_CACHE = "widget_cache"
    SEARCH_RESULTS = "search_results"
    ARCHIVE_PREVIEW = "archive_preview"
    ATTACHMENT_BUFFER = "attachment_buffer"
    DRAFT_STATE = "draft_state"
    RENDER_QUEUE = "render_queue"
    UNDO_HISTORY = "undo_history"
    LOG_BUFFER = "log_buffer"


@dataclass
class MemoryContract:
    max_widget_cache_bytes: int = 50 * 1024 * 1024
    max_search_results: int = 500
    max_archive_preview_items: int = 200
    max_attachment_buffer_kb: int = 10 * 1024
    max_draft_state_kb: int = 1024
    max_render_queue: int = 100
    max_undo_steps: int = 50
    max_log_buffer_kb: int = 512

    scope_limits: dict[MemoryScope, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.scope_limits:
            self.scope_limits = {
                MemoryScope.WIDGET_CACHE: self.max_widget_cache_bytes,
                MemoryScope.SEARCH_RESULTS: self.max_search_results,
                MemoryScope.ARCHIVE_PREVIEW: self.max_archive_preview_items,
                MemoryScope.ATTACHMENT_BUFFER: self.max_attachment_buffer_kb,
                MemoryScope.DRAFT_STATE: self.max_draft_state_kb,
                MemoryScope.RENDER_QUEUE: self.max_render_queue,
                MemoryScope.UNDO_HISTORY: self.max_undo_steps,
                MemoryScope.LOG_BUFFER: self.max_log_buffer_kb,
            }

    def limit_for(self, scope: MemoryScope) -> int:
        return self.scope_limits.get(scope, 0)

    def within_limit(self, scope: MemoryScope, current: int) -> bool:
        limit = self.limit_for(scope)
        if limit <= 0:
            return True
        return current <= limit
