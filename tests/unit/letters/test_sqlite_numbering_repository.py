from __future__ import annotations

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.application.letters.sqlite_numbering_repository import (
    SqliteNumberingRepository,
)


@pytest.fixture
def session() -> Session:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
    )
    with engine.connect() as raw:
        raw.execute(text("PRAGMA journal_mode = WAL"))
        raw.execute(text("PRAGMA synchronous = NORMAL"))
        raw.commit()

    SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    s = SessionLocal()
    try:
        yield s
        s.commit()
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()
        engine.dispose()


@pytest.fixture
def repo(session: Session) -> SqliteNumberingRepository:
    r = SqliteNumberingRepository(session)
    r.init_table()
    return r


class TestSqliteNumberingRepository:
    def test_init_table_creates_table(self, repo: SqliteNumberingRepository) -> None:
        repo.init_table()
        result = repo._session.execute(text(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='numbering_sequences'"
        ))
        assert result.fetchone() is not None

    def test_next_sequence_starts_at_one(self, repo: SqliteNumberingRepository) -> None:
        seq = repo.next_sequence("MOH", 2026)
        assert seq == 1

    def test_next_sequence_increments(self, repo: SqliteNumberingRepository) -> None:
        assert repo.next_sequence("MOH", 2026) == 1
        assert repo.next_sequence("MOH", 2026) == 2
        assert repo.next_sequence("MOH", 2026) == 3

    def test_next_sequence_per_prefix(self, repo: SqliteNumberingRepository) -> None:
        assert repo.next_sequence("MOH", 2026) == 1
        assert repo.next_sequence("LAB", 2026) == 1
        assert repo.next_sequence("ADM", 2026) == 1

    def test_next_sequence_per_year(self, repo: SqliteNumberingRepository) -> None:
        assert repo.next_sequence("MOH", 2026) == 1
        assert repo.next_sequence("MOH", 2027) == 1
        assert repo.next_sequence("MOH", 2026) == 2

    def test_next_sequence_batch(self, repo: SqliteNumberingRepository) -> None:
        seq = repo.next_sequence("MOH", 2026, count=5)
        assert seq == 1
        assert repo.next_sequence("MOH", 2026) == 6

    def test_get_current_sequence_nonexistent(
        self, repo: SqliteNumberingRepository
    ) -> None:
        seq = repo.get_current_sequence("MOH", 2026)
        assert seq is None

    def test_get_current_sequence_exists(
        self, repo: SqliteNumberingRepository
    ) -> None:
        repo.next_sequence("MOH", 2026)
        seq = repo.get_current_sequence("MOH", 2026)
        assert seq is not None
        assert seq.prefix == "MOH"
        assert seq.year == 2026
        assert seq.last_sequence == 1

    def test_reset_sequence(self, repo: SqliteNumberingRepository) -> None:
        repo.next_sequence("MOH", 2026)
        repo.reset_sequence("MOH", 2026, 100)
        seq = repo.next_sequence("MOH", 2026)
        assert seq == 101

    def test_sequence_exists(self, repo: SqliteNumberingRepository) -> None:
        assert repo.sequence_exists("MOH", 2026) is False
        repo.next_sequence("MOH", 2026)
        assert repo.sequence_exists("MOH", 2026) is True

    def test_list_sequences_empty(self, repo: SqliteNumberingRepository) -> None:
        assert repo.list_sequences() == []

    def test_list_sequences(self, repo: SqliteNumberingRepository) -> None:
        repo.next_sequence("MOH", 2026)
        repo.next_sequence("LAB", 2026)
        sequences = repo.list_sequences()
        assert len(sequences) == 2
        assert sequences[0].prefix == "LAB"
        assert sequences[1].prefix == "MOH"

    def test_deterministic_insert(self, repo: SqliteNumberingRepository) -> None:
        repo.next_sequence("MOH", 2026)
        repo.next_sequence("MOH", 2026)
        seq = repo.get_current_sequence("MOH", 2026)
        assert seq is not None
        assert seq.last_sequence == 2

    def test_unique_constraint(self, repo: SqliteNumberingRepository) -> None:
        repo.next_sequence("MOH", 2026)
        repo.reset_sequence("MOH", 2026, 50)
        seq = repo.get_current_sequence("MOH", 2026)
        assert seq is not None
        assert seq.last_sequence == 50

    def test_rollback_on_error(self, session: Session) -> None:
        repo = SqliteNumberingRepository(session)
        repo.init_table()
        repo.next_sequence("MOH", 2026)
        session.rollback()
        seq = repo.get_current_sequence("MOH", 2026)
        assert seq is None
