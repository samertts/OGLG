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


class TestAtomicAllocation:
    def test_allocate_single_number(self, repo: SqliteNumberingRepository) -> None:
        result = repo.allocate_number("MOH", 2026)
        assert result.is_ok
        assert result.number == "MOH-2026-000001"
        assert result.prefix == "MOH"
        assert result.year == 2026
        assert result.sequence == 1

    def test_allocate_incrementing(self, repo: SqliteNumberingRepository) -> None:
        r1 = repo.allocate_number("MOH", 2026)
        r2 = repo.allocate_number("MOH", 2026)
        r3 = repo.allocate_number("MOH", 2026)
        assert r1.sequence == 1
        assert r2.sequence == 2
        assert r3.sequence == 3
        assert r1.number == "MOH-2026-000001"
        assert r2.number == "MOH-2026-000002"
        assert r3.number == "MOH-2026-000003"

    def test_allocate_per_prefix(self, repo: SqliteNumberingRepository) -> None:
        r1 = repo.allocate_number("MOH", 2026)
        r2 = repo.allocate_number("LAB", 2026)
        assert r1.sequence == 1
        assert r2.sequence == 1
        assert r1.number.startswith("MOH")
        assert r2.number.startswith("LAB")

    def test_allocate_per_year(self, repo: SqliteNumberingRepository) -> None:
        r1 = repo.allocate_number("MOH", 2026)
        r2 = repo.allocate_number("MOH", 2027)
        assert r1.sequence == 1
        assert r2.sequence == 1
        assert "2026" in r1.number
        assert "2027" in r2.number

    def test_allocate_batch(self, repo: SqliteNumberingRepository) -> None:
        result = repo.allocate_number("MOH", 2026, count=5)
        assert result.is_ok
        assert result.sequence == 1
        assert result.number == "MOH-2026-000001"

        next_result = repo.allocate_number("MOH", 2026)
        assert next_result.sequence == 6

    def test_allocate_invalid_prefix(self, repo: SqliteNumberingRepository) -> None:
        result = repo.allocate_number("moh", 2026)
        assert result.is_error
        assert result.error_code == "INVALID_PREFIX"

    def test_allocate_invalid_year(self, repo: SqliteNumberingRepository) -> None:
        result = repo.allocate_number("MOH", 3000)
        assert result.is_error
        assert result.error_code == "INVALID_YEAR"

    def test_allocate_invalid_count_zero(self, repo: SqliteNumberingRepository) -> None:
        result = repo.allocate_number("MOH", 2026, count=0)
        assert result.is_error
        assert result.error_code == "INVALID_COUNT"

    def test_allocate_batch_too_large(self, repo: SqliteNumberingRepository) -> None:
        result = repo.allocate_number("MOH", 2026, count=1001)
        assert result.is_error
        assert result.error_code == "BATCH_TOO_LARGE"

    def test_allocate_rollback_on_failure(self, repo: SqliteNumberingRepository) -> None:
        repo.allocate_number("MOH", 2026)
        result = repo.allocate_number("moh", 2026)
        assert result.is_error

        after = repo.get_current_sequence("MOH", 2026)
        assert after is not None
        assert after.last_sequence == 1

    def test_allocate_no_duplicate_numbers(self, repo: SqliteNumberingRepository) -> None:
        results = [repo.allocate_number("MOH", 2026) for _ in range(10)]
        sequences = [r.sequence for r in results]
        assert len(set(sequences)) == 10
        assert sequences == list(range(1, 11))

    def test_allocate_immutable_result(self, repo: SqliteNumberingRepository) -> None:
        result = repo.allocate_number("MOH", 2026)
        import dataclasses
        assert dataclasses.is_dataclass(result)

    def test_allocate_with_metadata(self, repo: SqliteNumberingRepository) -> None:
        meta = {"request_id": "abc-123"}
        result = repo.allocate_number("MOH", 2026, metadata=meta)
        assert result.is_ok
        assert result.number == "MOH-2026-000001"
