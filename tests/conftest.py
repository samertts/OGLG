"""Shared test fixtures and configuration."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Generator

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.database.models import Base


@pytest.fixture
def tmp_db_path(tmp_path: Path) -> Path:
    return tmp_path / "test.db"


@pytest.fixture
def in_memory_engine() -> Generator[Any, None, None]:
    engine = create_engine("sqlite://", echo=False)
    Base.metadata.create_all(engine)

    @event.listens_for(engine, "connect")
    def set_pragmas(dbapi_connection: Any, connection_record: Any) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")
        cursor.execute("PRAGMA journal_mode = WAL")
        cursor.close()

    yield engine
    engine.dispose()


@pytest.fixture
def in_memory_session(in_memory_engine: Any) -> Generator[Session, None, None]:
    session_factory = sessionmaker(
        bind=in_memory_engine,
        expire_on_commit=False,
        autoflush=False,
    )
    session = session_factory()
    try:
        yield session
        session.rollback()
    finally:
        session.close()


@pytest.fixture
def data_dirs(tmp_path: Path) -> dict[str, Path]:
    return {
        "database": tmp_path / "database",
        "archives": tmp_path / "archives",
        "backups": tmp_path / "backups",
        "generated_letters": tmp_path / "generated_letters",
        "attachments": tmp_path / "attachments",
        "logs": tmp_path / "logs",
        "temp": tmp_path / "temp",
    }
