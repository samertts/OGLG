from __future__ import annotations

from typing import Any, Protocol

from app.application.letters.dto import LetterResultDTO, SearchLetterDTO, SearchResultDTO


class SearchIndex(Protocol):
    def search(self, query: str, offset: int = 0, limit: int = 50) -> list[dict[str, Any]]: ...
    def search_advanced(self, filters: dict[str, Any], offset: int = 0, limit: int = 50) -> list[dict[str, Any]]: ...
    def count(self, query: str) -> int: ...
    def count_advanced(self, filters: dict[str, Any]) -> int: ...
    def index_letter(self, letter_id: str, subject: str, body: str, number: str, sender: str, department: str, language: str) -> None: ...
    def remove_letter(self, letter_id: str) -> None: ...


class SearchService:
    def __init__(self, search_index: SearchIndex, letter_repo: Any) -> None:
        self._index = search_index
        self._letter_repo = letter_repo

    def search(self, dto: SearchLetterDTO) -> SearchResultDTO:
        filters: dict[str, Any] = {}
        if dto.query:
            filters["query"] = dto.query
        if dto.status:
            filters["status"] = dto.status.value
        if dto.letter_type:
            filters["letter_type"] = dto.letter_type.value
        if dto.priority:
            filters["priority"] = dto.priority.value
        if dto.classification:
            filters["classification"] = dto.classification.value
        if dto.department_id:
            filters["department_id"] = dto.department_id
        if dto.sender_id:
            filters["sender_id"] = dto.sender_id
        if dto.date_from:
            filters["date_from"] = dto.date_from.isoformat()
        if dto.date_to:
            filters["date_to"] = dto.date_to.isoformat()

        if dto.query:
            total = self._index.count(dto.query) if not filters else 0
            raw = self._index.search(dto.query, dto.offset, dto.limit) if not filters else []
        else:
            total = self._index.count_advanced(filters)
            raw = self._index.search_advanced(filters, dto.offset, dto.limit)

        results: list[LetterResultDTO] = []
        for item in raw:
            letter = self._letter_repo.get_by_id(item.get("letter_id", ""))
            if letter:
                results.append(LetterResultDTO.from_aggregate(letter))

        return SearchResultDTO(total=total, offset=dto.offset, limit=dto.limit, results=results)

    def index_letter(self, letter_id: str, subject: str, body: str, number: str, sender: str, department: str, language: str) -> None:
        self._index.index_letter(letter_id, subject, body, number, sender, department, language)

    def remove_from_index(self, letter_id: str) -> None:
        self._index.remove_letter(letter_id)
