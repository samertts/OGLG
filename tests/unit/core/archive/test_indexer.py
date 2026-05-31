from __future__ import annotations

from pathlib import Path

from app.core.archive.indexer import ArchiveIndexer
from app.core.archive.snapshot import ArchiveSnapshot
from app.core.archive.validator import ArchiveIntegrityValidator


def test_indexer_index_and_lookup(tmp_path: Path) -> None:
    db = tmp_path / "archive.db"
    indexer = ArchiveIndexer(db)
    indexer.open()

    snap = ArchiveSnapshot(
        archive_type="letter",
        source_id="L001",
        data={"subject": "Test"},
    )
    sid = indexer.index(snap)
    assert sid == snap.snapshot_id
    assert indexer.count == 1

    loaded = indexer.lookup(sid)
    assert loaded is not None
    assert loaded.archive_type == "letter"
    assert loaded.source_id == "L001"
    indexer.close()


def test_indexer_verify_integrity(tmp_path: Path) -> None:
    db = tmp_path / "archive.db"
    indexer = ArchiveIndexer(db)
    indexer.open()

    snap = ArchiveSnapshot(
        archive_type="letter",
        source_id="L002",
        data={"content": "Hello World"},
    )
    sid = indexer.index(snap)
    assert indexer.verify_integrity(sid)
    indexer.close()


def test_indexer_link_attachment(tmp_path: Path) -> None:
    db = tmp_path / "archive.db"
    indexer = ArchiveIndexer(db)
    indexer.open()

    snap = ArchiveSnapshot(archive_type="letter", source_id="L003")
    sid = indexer.index(snap)
    indexer.link_attachment(sid, "doc.pdf", "abc123", file_size=1024)
    indexer.close()


def test_validator(tmp_path: Path) -> None:
    db = tmp_path / "archive.db"
    indexer = ArchiveIndexer(db)
    indexer.open()

    snap = ArchiveSnapshot(
        archive_type="letter",
        source_id="L004",
        data={"body": "Valid content"},
    )
    sid = indexer.index(snap)

    validator = ArchiveIntegrityValidator(indexer)
    result = validator.validate(sid)
    assert result["valid"]
    assert not result["corrupted"]
    indexer.close()
