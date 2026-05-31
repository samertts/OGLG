from __future__ import annotations

from pathlib import Path

from app.core.search.engine import SearchEngine, SearchQuery


def test_search_index_and_query(tmp_path: Path) -> None:
    db = tmp_path / "search.db"
    engine = SearchEngine(db)
    engine.open()

    engine.index_document(
        snapshot_id="s1",
        archive_type="letter",
        source_id="L001",
        sender="Ministry of Health",
        subject="Annual Report",
        body="This is the annual report for 2026",
    )
    engine.index_document(
        snapshot_id="s2",
        archive_type="memo",
        source_id="M001",
        sender="HR Department",
        subject="Staff Meeting",
        body="Meeting scheduled for next week",
    )

    assert engine.document_count == 2

    query = SearchQuery(text="annual")
    results = engine.search(query)
    assert len(results) == 1
    assert results[0].snapshot_id == "s1"
    engine.close()


def test_search_pagination(tmp_path: Path) -> None:
    db = tmp_path / "search.db"
    engine = SearchEngine(db, max_results=100)
    engine.open()

    for i in range(10):
        engine.index_document(
            snapshot_id=f"s{i}",
            archive_type="letter",
            source_id=f"L{i:03d}",
            subject=f"Document {i}",
            body=f"Content of document number {i}",
        )

    query = SearchQuery(text="document", page=0, page_size=3)
    results = engine.search(query)
    assert len(results) == 3

    query.page = 1
    results = engine.search(query)
    assert len(results) == 3

    query.page = 3
    results = engine.search(query)
    assert len(results) == 1
    engine.close()


def test_search_filter_by_type(tmp_path: Path) -> None:
    db = tmp_path / "search.db"
    engine = SearchEngine(db)
    engine.open()

    engine.index_document(
        snapshot_id="s1", archive_type="letter", source_id="L001"
    )
    engine.index_document(
        snapshot_id="s2", archive_type="memo", source_id="M001"
    )

    query = SearchQuery(archive_type="letter")
    results = engine.search(query)
    assert len(results) == 1
    assert results[0].archive_type == "letter"
    engine.close()


def test_search_arabic_normalization(tmp_path: Path) -> None:
    db = tmp_path / "search.db"
    engine = SearchEngine(db)
    engine.open()

    engine.index_document(
        snapshot_id="s1",
        archive_type="letter",
        source_id="L001",
        subject="تقارير وزارة الصحة",
        body="هذا تقرير عن نشاطات الوزارة",
    )

    query = SearchQuery(text="تقرير")
    results = engine.search(query)
    assert len(results) == 1
    engine.close()


def test_search_state(tmp_path: Path) -> None:
    db = tmp_path / "search.db"
    engine = SearchEngine(db)
    engine.open()
    state = engine.state()
    assert state["open"] is True
    assert state["document_count"] == 0
    engine.close()
