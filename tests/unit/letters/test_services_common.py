from __future__ import annotations

from datetime import datetime
from typing import Any

from app.domain.letters.events import DomainEvent
from app.domain.letters.letter import Letter
from app.domain.letters.letter_status import LetterStatus


class InMemoryLetterRepo:
    def __init__(self) -> None:
        self._letters: dict[str, Letter] = {}

    def save(self, letter: Letter) -> None:
        self._letters[letter.id] = letter

    def get_by_id(self, letter_id: str) -> Letter | None:
        return self._letters.get(letter_id)

    def get_by_number(self, number: str) -> Letter | None:
        for letter in self._letters.values():
            if letter.number == number:
                return letter
        return None

    def delete(self, letter_id: str) -> None:
        self._letters.pop(letter_id, None)

    def list_by_department(self, department_id: str, offset: int = 0, limit: int = 50) -> list[Letter]:
        items = [letter for letter in self._letters.values() if letter.department_id == department_id]
        return items[offset:offset + limit]

    def list_by_status(self, status: LetterStatus, offset: int = 0, limit: int = 50) -> list[Letter]:
        items = [letter for letter in self._letters.values() if letter.status == status]
        return items[offset:offset + limit]

    def list_by_date_range(self, start: datetime, end: datetime, offset: int = 0, limit: int = 50) -> list[Letter]:
        items = [letter for letter in self._letters.values() if start <= letter.created_at <= end]
        return items[offset:offset + limit]

    def count_by_department(self, department_id: str) -> int:
        return sum(1 for letter in self._letters.values() if letter.department_id == department_id)

    def count_by_status(self, status: LetterStatus) -> int:
        return sum(1 for letter in self._letters.values() if letter.status == status)


class InMemoryAuditRepo:
    def __init__(self) -> None:
        self.events: list[DomainEvent] = []

    def append(self, event: DomainEvent) -> None:
        self.events.append(event)

    def get_events_for_letter(self, letter_id: str) -> list[DomainEvent]:
        return [e for e in self.events if e.aggregate_id == letter_id]

    def get_events_by_user(self, user_id: str, limit: int = 50) -> list[DomainEvent]:
        return [e for e in self.events if e.user_id == user_id][:limit]


class InMemoryUoW:
    def __init__(self) -> None:
        self.committed = False
        self.rolled_back = False

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        self.rolled_back = True

    def flush(self) -> None:
        pass

    def __enter__(self) -> InMemoryUoW:
        return self

    def __exit__(self, *args: Any) -> None:
        pass


def make_draft_letter(
    letter_id: str | None = None,
    sender_id: str = "user-1",
    department_id: str = "dept-1",
) -> Letter:
    letter = Letter.create(
        letter_type="OUTGOING",
        subject="Test Subject",
        body="Test body content",
        sender_id=sender_id,
        sender_name="Test User",
        sender_department="Test Dept",
        department_id=department_id,
        created_by_id=sender_id,
    )
    if letter_id:
        letter.id = letter_id
    letter.pop_events()
    return letter
