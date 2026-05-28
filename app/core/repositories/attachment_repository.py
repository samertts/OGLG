from __future__ import annotations

from abc import abstractmethod
from typing import Protocol
from uuid import UUID

from app.core.entities.attachment import Attachment


class AttachmentRepository(Protocol):
    """Repository interface for Attachment entities."""

    @abstractmethod
    def find_by_id(self, id: UUID) -> Attachment | None:
        ...

    @abstractmethod
    def find_by_letter(self, letter_id: UUID) -> list[Attachment]:
        ...

    @abstractmethod
    def save(self, attachment: Attachment) -> Attachment:
        ...

    @abstractmethod
    def delete(self, id: UUID) -> None:
        ...

    @abstractmethod
    def delete_by_letter(self, letter_id: UUID) -> int:
        ...
