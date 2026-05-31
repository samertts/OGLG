from __future__ import annotations

from pathlib import Path

from app.core.recovery.engine import RecoveryEngine
from app.core.recovery.validator import WalRecoveryValidator


def test_recovery_engine_assess(tmp_path: Path) -> None:
    import sqlite3
    db_path = tmp_path / "healthy.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute("CREATE TABLE t (id INTEGER PRIMARY KEY)")
    conn.close()

    validator = WalRecoveryValidator(db_path)
    engine = RecoveryEngine(validator)
    result = engine.assess()
    assert "validation" in result
    assert "recommendations" in result
    assert len(result["recommendations"]) > 0
    assert result["recovery_attempts"] == 0


def test_recovery_engine_attempt(tmp_path: Path) -> None:
    import sqlite3
    db_path = tmp_path / "healthy.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute("CREATE TABLE t (id INTEGER PRIMARY KEY)")
    conn.close()

    validator = WalRecoveryValidator(db_path)
    engine = RecoveryEngine(validator)
    result = engine.attempt_recovery()
    assert result["attempt"] == 1
    assert result["status"] == "completed"
