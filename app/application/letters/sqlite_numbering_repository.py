from __future__ import annotations

from datetime import datetime

from sqlalchemy import text
from sqlalchemy.orm import Session

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


__all__ = [
    "SqliteNumberingRepository",
]
