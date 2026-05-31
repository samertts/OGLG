from __future__ import annotations

import struct

from app.core.diagnostics.wal_check import WalConsistencyChecker


def test_wal_not_exists() -> None:
    checker = WalConsistencyChecker("/tmp/nonexistent_wal_file.db-wal")
    result = checker.check()
    assert result["valid"] is True
    assert result["exists"] is False


def test_wal_valid_header(tmp_path) -> None:
    wal_path = tmp_path / "test.db-wal"
    header = bytearray(36)
    header[:16] = b"SQLite format 3\x00"
    struct.pack_into(">I", header, 16, 3007000)
    struct.pack_into(">I", header, 20, 4096)
    struct.pack_into(">I", header, 24, 42)
    struct.pack_into(">I", header, 28, 12345)
    struct.pack_into(">I", header, 32, 67890)
    wal_path.write_bytes(bytes(header))

    checker = WalConsistencyChecker(wal_path)
    result = checker.check()
    assert result["valid"] is True
    assert result["exists"] is True
    assert result["version"] == 3007000
    assert result["page_size"] == 4096
    assert result["checkpoint_sequence"] == 42


def test_wal_bad_magic(tmp_path) -> None:
    wal_path = tmp_path / "bad.db-wal"
    wal_path.write_bytes(b"BAD HEADER DATA" + b"\x00" * 22)

    checker = WalConsistencyChecker(wal_path)
    result = checker.check()
    assert result["valid"] is False
    assert "Invalid WAL magic" in result["message"]


def test_wal_truncated(tmp_path) -> None:
    wal_path = tmp_path / "truncated.db-wal"
    wal_path.write_bytes(b"too short")

    checker = WalConsistencyChecker(wal_path)
    result = checker.check()
    assert result["valid"] is False
