from __future__ import annotations

from app.ui.core.archive_browser import ArchiveBrowseState, ArchiveEntryPreview, PreviewState
from app.ui.core.search_models import (
    SearchFilterState,
    SearchPaginationState,
    SearchResultItem,
    SearchSessionState,
)


class TestSearchFilterState:
    def test_defaults(self):
        f = SearchFilterState()
        assert f.query == ""
        assert f.arabic_normalize

    def test_is_active_with_query(self):
        f = SearchFilterState(query="test")
        assert f.is_active()

    def test_is_active_inactive(self):
        f = SearchFilterState()
        assert not f.is_active()

    def test_clear(self):
        f = SearchFilterState(query="test", sender="user")
        f.clear()
        assert not f.is_active()

    def test_is_active_with_sender(self):
        f = SearchFilterState(sender="ministry")
        assert f.is_active()

    def test_is_active_with_date(self):
        f = SearchFilterState(date_from="2026-01-01")
        assert f.is_active()


class TestSearchPaginationState:
    def test_defaults(self):
        p = SearchPaginationState()
        assert p.page == 0
        assert p.page_size == 20
        assert not p.has_next
        assert not p.has_previous

    def test_offset(self):
        p = SearchPaginationState(page=2, page_size=10)
        assert p.offset == 20

    def test_has_next(self):
        p = SearchPaginationState(page=0, total_pages=3)
        assert p.has_next

    def test_no_next_on_last_page(self):
        p = SearchPaginationState(page=2, total_pages=3)
        assert not p.has_next

    def test_has_previous(self):
        p = SearchPaginationState(page=1)
        assert p.has_previous

    def test_next_page(self):
        p = SearchPaginationState(page=0, total_pages=3)
        p.next_page()
        assert p.page == 1

    def test_previous_page(self):
        p = SearchPaginationState(page=2)
        p.previous_page()
        assert p.page == 1

    def test_reset(self):
        p = SearchPaginationState(page=3, total_results=50, total_pages=5)
        p.reset()
        assert p.page == 0
        assert p.total_results == 0

    def test_update_from_count(self):
        p = SearchPaginationState(page=0, page_size=10)
        p.update_from_count(25)
        assert p.total_results == 25
        assert p.total_pages == 3

    def test_update_from_count_clamps_page(self):
        p = SearchPaginationState(page=5, page_size=10)
        p.update_from_count(5)
        assert p.page == 0

    def test_update_from_count_zero(self):
        p = SearchPaginationState(page=0, page_size=10)
        p.update_from_count(0)
        assert p.total_pages == 1
        assert p.total_results == 0


class TestSearchSessionState:
    def test_defaults(self):
        s = SearchSessionState()
        assert not s.searching
        assert s.error is None
        assert len(s.results) == 0

    def _make_result(self, row_id=1, sid="s1"):
        return SearchResultItem(
            row_id=row_id, snapshot_id=sid,
            archive_type="letter", source_id="src1",
            snippet="hello",
        )

    def test_set_results(self):
        s = SearchSessionState()
        items = [self._make_result()]
        s.set_results(items, 1)
        assert len(s.results) == 1
        assert s.pagination.total_results == 1
        assert not s.searching

    def test_clear(self):
        s = SearchSessionState()
        items = [self._make_result()]
        s.set_results(items, 1)
        s.searching = True
        s.clear()
        assert len(s.results) == 0
        assert not s.searching

    def test_last_query_id_increments(self):
        s = SearchSessionState()
        items = [self._make_result()]
        s.set_results(items, 1)
        assert s.last_query_id == 1
        s.set_results(items, 1)
        assert s.last_query_id == 2


class TestArchiveBrowseState:
    def test_defaults(self):
        b = ArchiveBrowseState()
        assert b.page == 0
        assert not b.loading
        assert b.error is None

    def _make_entry(self, eid="1", sid="s1"):
        return ArchiveEntryPreview(
            entry_id=eid, snapshot_id=sid,
            archive_type="letter", source_id="src1",
            checksum="abc",
        )

    def test_total_pages(self):
        b = ArchiveBrowseState(page_size=10)
        b.set_entries([self._make_entry()], 25)
        assert b.total_pages == 3

    def test_has_next(self):
        b = ArchiveBrowseState(page=0, page_size=10)
        b.set_entries([], 25)
        assert b.has_next

    def test_no_next_on_last(self):
        b = ArchiveBrowseState(page=2, page_size=10)
        b.set_entries([], 25)
        assert not b.has_next

    def test_next_page(self):
        b = ArchiveBrowseState(page=0, page_size=10)
        b.set_entries([], 25)
        b.next_page()
        assert b.page == 1

    def test_previous_page(self):
        b = ArchiveBrowseState(page=2)
        b.previous_page()
        assert b.page == 1

    def test_set_entries_clears_error(self):
        b = ArchiveBrowseState()
        b.error = "previous error"
        b.set_entries([self._make_entry()], 1)
        assert b.error is None

    def test_clear(self):
        b = ArchiveBrowseState()
        b.set_entries([self._make_entry()], 1)
        b.clear()
        assert len(b.entries) == 0
        assert b.page == 0


class TestPreviewState:
    def test_defaults(self):
        p = PreviewState()
        assert p.preview_type == ""
        assert p.error is None

    def test_set_preview(self):
        p = PreviewState()
        p.set_preview("archive", "ARC-001", "Test Document", "content here", source="ministry")
        assert p.preview_type == "archive"
        assert p.item_id == "ARC-001"
        assert p.title == "Test Document"
        assert p.metadata["source"] == "ministry"

    def test_clear(self):
        p = PreviewState()
        p.set_preview("archive", "ARC-001", "Test", "content")
        p.clear()
        assert p.preview_type == ""
        assert not p.metadata
