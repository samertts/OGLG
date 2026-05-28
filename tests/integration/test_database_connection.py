"""Integration tests for database connection and lifecycle."""

from pathlib import Path

import pytest

from app.database.connection import DatabaseManager, create_database_engine, create_session_factory
from app.database.models import Base


class TestDatabaseEngine:
    def test_engine_creation(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.db"
        engine = create_database_engine(db_path)
        assert engine is not None
        engine.dispose()

    def test_engine_applies_wal(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.db"
        engine = create_database_engine(db_path)
        with engine.connect() as conn:
            row = conn.execute(__import__("sqlalchemy").text("PRAGMA journal_mode")).fetchone()
            assert row[0] == "wal"
        engine.dispose()

    def test_engine_applies_foreign_keys(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.db"
        engine = create_database_engine(db_path)
        with engine.connect() as conn:
            row = conn.execute(__import__("sqlalchemy").text("PRAGMA foreign_keys")).fetchone()
            assert row[0] == 1
        engine.dispose()


class TestDatabaseManager:
    def test_initialize(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.db"
        mgr = DatabaseManager(db_path)
        mgr.initialize()
        assert mgr.engine is not None
        assert mgr.session_factory is not None
        mgr.dispose()

    def test_verify_integrity_ok(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.db"
        mgr = DatabaseManager(db_path)
        mgr.initialize()
        Base.metadata.create_all(mgr.engine)
        assert mgr.verify_integrity()
        mgr.dispose()

    def test_get_table_names(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.db"
        mgr = DatabaseManager(db_path)
        mgr.initialize()
        Base.metadata.create_all(mgr.engine)
        tables = mgr.get_table_names()
        assert "letters" in tables
        assert "users" in tables
        assert "departments" in tables
        mgr.dispose()

    def test_vacuum(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.db"
        mgr = DatabaseManager(db_path)
        mgr.initialize()
        Base.metadata.create_all(mgr.engine)
        mgr.vacuum()
        mgr.dispose()

    def test_backup_to(self, tmp_path: Path) -> None:
        db_path = tmp_path / "source.db"
        backup_path = tmp_path / "backup.db"
        mgr = DatabaseManager(db_path)
        mgr.initialize()
        Base.metadata.create_all(mgr.engine)
        mgr.backup_to(backup_path)
        assert backup_path.exists()
        assert backup_path.stat().st_size > 0
        mgr.dispose()

    def test_dispose(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.db"
        mgr = DatabaseManager(db_path)
        mgr.initialize()
        mgr.dispose()
        assert mgr.engine is not None

    def test_not_initialized_raises(self, tmp_path: Path) -> None:
        mgr = DatabaseManager(tmp_path / "nope.db")
        with pytest.raises(RuntimeError, match="not initialized"):
            mgr.verify_integrity()


class TestSessionFactory:
    def test_session_creation(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.db"
        engine = create_database_engine(db_path)
        Base.metadata.create_all(engine)
        session_factory = create_session_factory(engine)
        session = session_factory()
        assert session is not None
        session.close()
        engine.dispose()

    def test_session_rollback_on_error(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.db"
        engine = create_database_engine(db_path)
        Base.metadata.create_all(engine)
        session_factory = create_session_factory(engine)
        session = session_factory()
        try:
            session.execute(__import__("sqlalchemy").text("INVALID SQL"))
            session.commit()
        except Exception:
            session.rollback()
        session.close()
        engine.dispose()
