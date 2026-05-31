from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class ArchiveLink:
    letter_id: str
    archive_entry_id: str
    linked_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)


class ArchiveLinker:
    def __init__(self, max_links: int = 10_000):
        self._links: dict[str, list[ArchiveLink]] = {}
        self._max_links = max_links

    @property
    def total_links(self) -> int:
        return sum(len(links) for links in self._links.values())

    def link(self, letter_id: str, archive_entry_id: str, **metadata: Any) -> ArchiveLink | None:
        if self.total_links >= self._max_links:
            return None
        link = ArchiveLink(
            letter_id=letter_id, archive_entry_id=archive_entry_id,
            metadata=metadata,
        )
        if letter_id not in self._links:
            self._links[letter_id] = []
        self._links[letter_id].append(link)
        return link

    def unlink(self, letter_id: str, archive_entry_id: str) -> bool:
        links = self._links.get(letter_id)
        if links is None:
            return False
        before = len(links)
        self._links[letter_id] = [
            ln for ln in links if ln.archive_entry_id != archive_entry_id
        ]
        return len(self._links[letter_id]) < before

    def get_links(self, letter_id: str) -> list[ArchiveLink]:
        return list(self._links.get(letter_id, []))

    def get_letters_for_archive_entry(self, archive_entry_id: str) -> list[str]:
        result: list[str] = []
        for letter_id, links in self._links.items():
            for link in links:
                if link.archive_entry_id == archive_entry_id:
                    result.append(letter_id)
        return result

    def clear(self) -> None:
        self._links.clear()
