from __future__ import annotations

import sqlite3
from pathlib import Path

from app.core.recovery.validator import WalRecoveryValidator


def test_validator_healthy_db(tmp_path: Path) -> None:
    db_path = tmp_path / "healthy.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute("CREATE TABLE test (id INTEGER PRIMARY KEY)")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.close()

    validator = WalRecoveryValidator(db_path)
    result = validator.validate()
    assert result["database_ok"] is True
    assert result["recovery_needed"] is False


def test_validator_missing_db(tmp_path: Path) -> None:
    db_path = tmp_path / "missing.db"
    validator = WalRecoveryValidator(db_path)
    result = validator.validate()
    assert result["database_ok"] is False


def test_validator_corrupt_db(tmp_path: Path) -> None:
    db_path = tmp_path / "corrupt.db"
    db_path.write_bytes(b"not a valid sqlite database")
    validator = WalRecoveryValidator(db_path)
    result = validator.validate()
    assert result["database_ok"] is False
