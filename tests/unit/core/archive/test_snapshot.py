from __future__ import annotations

from app.core.archive.snapshot import ArchiveSnapshot


def test_snapshot_defaults() -> None:
    snap = ArchiveSnapshot()
    assert snap.snapshot_id is not None
    assert snap.archive_type == ""


def test_snapshot_checksum() -> None:
    snap = ArchiveSnapshot(
        archive_type="letter",
        source_id="L001",
        data={"subject": "Test"},
    )
    ck = snap.compute_checksum()
    assert len(ck) == 64
    assert ck == snap.compute_checksum()


def test_snapshot_with_checksum() -> None:
    snap = ArchiveSnapshot(
        archive_type="letter",
        source_id="L002",
        data={"content": "hello"},
    )
    validated = snap.with_checksum()
    assert validated.checksum == snap.compute_checksum()


def test_snapshot_to_dict() -> None:
    snap = ArchiveSnapshot(
        archive_type="letter",
        source_id="L003",
        data={"ref": "123"},
    ).with_checksum()
    d = snap.to_dict()
    assert d["archive_type"] == "letter"
    assert d["source_id"] == "L003"
    assert "checksum" in d
