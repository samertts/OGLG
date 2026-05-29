from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.application.letters.numbering_policy import (
    format_number,
    validate_prefix,
    validate_year,
)
from app.application.letters.numbering_result import NumberingResult
from app.application.letters.numbering_sequence import NumberingSequence


class SqliteNumberingRepository:
    _TABLE = "numbering_sequences"

    def __init__(self, session: Session) -> None:
        self._session = session

    def init_table(self) -> None:
        self._session.execute(text(f"""
            CREATE TABLE IF NOT EXISTS {self._TABLE} (
                prefix TEXT NOT NULL,
                year INTEGER NOT NULL,
                last_sequence INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT,
                PRIMARY KEY (prefix, year)
            )
        """))
        self._session.flush()

    def next_sequence(self, prefix: str, year: int, count: int = 1) -> int:
        self._session.execute(text(f"""
            INSERT OR IGNORE INTO {self._TABLE} (prefix, year, last_sequence)
            VALUES (:prefix, :year, 0)
        """), {"prefix": prefix, "year": year})

        result = self._session.execute(text(f"""
            UPDATE {self._TABLE}
            SET last_sequence = last_sequence + :count,
                updated_at = datetime('now')
            WHERE prefix = :prefix AND year = :year
            RETURNING last_sequence
        """), {"prefix": prefix, "year": year, "count": count})

        row = result.fetchone()
        if row is None:
            raise RuntimeError(f"sequence update failed for {prefix}-{year}")

        return row[0] - count + 1

    def get_current_sequence(self, prefix: str, year: int) -> NumberingSequence | None:
        result = self._session.execute(text(f"""
            SELECT prefix, year, last_sequence, created_at, updated_at
            FROM {self._TABLE}
            WHERE prefix = :prefix AND year = :year
        """), {"prefix": prefix, "year": year})

        row = result.fetchone()
        if row is None:
            return None

        return NumberingSequence(
            prefix=row[0],
            year=row[1],
            last_sequence=row[2],
            created_at=(
                datetime.fromisoformat(row[3]) if isinstance(row[3], str) else row[3]
            ),
            updated_at=(
                datetime.fromisoformat(row[4])
                if row[4] and isinstance(row[4], str)
                else row[4]
            ),
        )

    def reset_sequence(self, prefix: str, year: int, value: int = 0) -> None:
        self._session.execute(text(f"""
            INSERT OR REPLACE INTO {self._TABLE} (prefix, year, last_sequence, updated_at)
            VALUES (:prefix, :year, :value, datetime('now'))
        """), {"prefix": prefix, "year": year, "value": value})
        self._session.flush()

    def sequence_exists(self, prefix: str, year: int) -> bool:
        result = self._session.execute(text(f"""
            SELECT 1 FROM {self._TABLE}
            WHERE prefix = :prefix AND year = :year
        """), {"prefix": prefix, "year": year})
        return result.fetchone() is not None

    def list_sequences(self) -> list[NumberingSequence]:
        result = self._session.execute(text(f"""
            SELECT prefix, year, last_sequence, created_at, updated_at
            FROM {self._TABLE}
            ORDER BY prefix, year
        """))
        sequences: list[NumberingSequence] = []
        for row in result:
            sequences.append(NumberingSequence(
                prefix=row[0],
                year=row[1],
                last_sequence=row[2],
                created_at=(
                    datetime.fromisoformat(row[3]) if isinstance(row[3], str) else row[3]
                ),
                updated_at=(
                    datetime.fromisoformat(row[4])
                    if row[4] and isinstance(row[4], str)
                    else row[4]
                ),
            ))
        return sequences


    def allocate_number(
        self,
        prefix: str,
        year: int,
        count: int = 1,
        metadata: dict[str, Any] | None = None,
    ) -> NumberingResult:
        prefix_err = validate_prefix(prefix)
        if prefix_err:
            return NumberingResult.fail(prefix_err, error_code="INVALID_PREFIX")

        year_err = validate_year(year)
        if year_err:
            return NumberingResult.fail(year_err, error_code="INVALID_YEAR")

        if count < 1:
            return NumberingResult.fail(
                "count must be at least 1", error_code="INVALID_COUNT"
            )
        if count > 1000:
            return NumberingResult.fail(
                "count cannot exceed 1000", error_code="BATCH_TOO_LARGE"
            )

        try:
            with self._session.begin_nested():
                self._session.execute(text(f"""
                    INSERT OR IGNORE INTO {self._TABLE}
                    (prefix, year, last_sequence)
                    VALUES (:prefix, :year, 0)
                """), {"prefix": prefix, "year": year})

                result = self._session.execute(text(f"""
                    UPDATE {self._TABLE}
                    SET last_sequence = last_sequence + :count,
                        updated_at = datetime('now')
                    WHERE prefix = :prefix AND year = :year
                    RETURNING last_sequence
                """), {"prefix": prefix, "year": year, "count": count})

                row = result.fetchone()
                if row is None:
                    raise RuntimeError(f"sequence update failed for {prefix}-{year}")

                seq = row[0] - count + 1
                number = format_number(prefix, year, seq)

            self._session.commit()

            return NumberingResult.ok(
                number=number,
                prefix=prefix,
                year=year,
                sequence=seq,
                metadata=metadata,
            )
        except Exception as exc:
            self._session.rollback()
            return NumberingResult.fail(
                str(exc), error_code="ALLOCATION_FAILED"
            )


class ConcurrentAllocationHook(ABC):
    @abstractmethod
    def on_allocation_start(self, prefix: str, year: int, count: int) -> None:
        ...

    @abstractmethod
    def on_allocation_commit(
        self, prefix: str, year: int, sequence: int, number: str
    ) -> None:
        ...

    @abstractmethod
    def on_allocation_rollback(self, prefix: str, year: int, error: str) -> None:
        ...


__all__ = [
    "SqliteNumberingRepository",
    "ConcurrentAllocationHook",
]
