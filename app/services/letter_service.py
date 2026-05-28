"""Letter service — business operations for the Letter aggregate."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
from uuid import UUID, uuid4

from app.core.entities.letter import Letter
from app.core.enums import LetterStatus
from app.core.exceptions.base import (
    BusinessRuleViolation,
    EntityNotFoundError,
    ValidationError,
)
from app.core.repositories.letter_repository import LetterRepository
from app.services.dto import (
    LetterCreateDTO,
    LetterResponseDTO,
    LetterUpdateDTO,
    PaginatedResult,
)
from app.utils.logger import get_logger

logger = get_logger("app.services.letter_service")


@dataclass
class LetterService:
    letter_repo: LetterRepository

    def create_letter(self, dto: LetterCreateDTO) -> LetterResponseDTO:
        if not dto.subject.strip():
            raise ValidationError("Letter subject is required")
        if not dto.body.strip():
            raise ValidationError("Letter body is required")

        year = datetime.now().year
        seq = self.letter_repo.next_sequence_for_year(year)
        number = f"{year}-{seq:04d}"

        content_hash = sha256((dto.subject + dto.body).encode("utf-8")).hexdigest()

        entity = Letter(
            id=uuid4(),
            number=number,
            subject=dto.subject,
            body=dto.body,
            sender_name=dto.sender_name,
            sender_title=dto.sender_title,
            recipient_name=dto.recipient_name,
            recipient_title=dto.recipient_title,
            recipient_dept=dto.recipient_dept,
            department_id=dto.department_id,
            priority=dto.priority,
            status=LetterStatus.DRAFT,
            language=dto.language,
            reference_number=dto.reference_number,
            created_by_id=dto.created_by_id,
            created_at=datetime.now(),
            content_hash=content_hash,
        )
        saved = self.letter_repo.save(entity)
        logger.info("Letter created", extra={"number": number, "id": str(saved.id)})
        return LetterResponseDTO.from_entity(saved)

    def get_letter(self, letter_id: UUID) -> LetterResponseDTO:
        entity = self.letter_repo.find_by_id(letter_id)
        if not entity:
            raise EntityNotFoundError(f"Letter not found: {letter_id}")
        return LetterResponseDTO.from_entity(entity)

    def update_letter(self, letter_id: UUID, dto: LetterUpdateDTO) -> LetterResponseDTO:
        entity = self.letter_repo.find_by_id(letter_id)
        if not entity:
            raise EntityNotFoundError(f"Letter not found: {letter_id}")
        if entity.status == LetterStatus.ARCHIVED:
            raise BusinessRuleViolation("Cannot modify an archived letter")

        for field_name, value in {
            "subject": dto.subject,
            "body": dto.body,
            "sender_name": dto.sender_name,
            "sender_title": dto.sender_title,
            "recipient_name": dto.recipient_name,
            "recipient_title": dto.recipient_title,
            "recipient_dept": dto.recipient_dept,
            "department_id": dto.department_id,
            "priority": dto.priority,
            "language": dto.language,
            "reference_number": dto.reference_number,
        }.items():
            if value is not None:
                setattr(entity, field_name, value)

        entity.mark_updated(dto.updated_by_id or entity.created_by_id)
        entity.content_hash = sha256((entity.subject + entity.body).encode("utf-8")).hexdigest()

        saved = self.letter_repo.save(entity)
        logger.info("Letter updated", extra={"id": str(letter_id)})
        return LetterResponseDTO.from_entity(saved)

    def delete_letter(self, letter_id: UUID, user_id: UUID) -> None:
        entity = self.letter_repo.find_by_id(letter_id)
        if not entity:
            raise EntityNotFoundError(f"Letter not found: {letter_id}")
        entity.soft_delete(user_id)
        self.letter_repo.save(entity)
        logger.info("Letter soft-deleted", extra={"id": str(letter_id)})

    def archive_letter(self, letter_id: UUID, user_id: UUID) -> LetterResponseDTO:
        entity = self.letter_repo.find_by_id(letter_id)
        if not entity:
            raise EntityNotFoundError(f"Letter not found: {letter_id}")
        if entity.is_archived:
            raise BusinessRuleViolation("Letter is already archived")
        entity.archive(user_id)
        saved = self.letter_repo.save(entity)
        logger.info("Letter archived", extra={"id": str(letter_id)})
        return LetterResponseDTO.from_entity(saved)

    def search_letters(
        self, query: str, offset: int = 0, limit: int = 50
    ) -> PaginatedResult[LetterResponseDTO]:
        items = self.letter_repo.search(query, offset, limit)
        total = self.letter_repo.count_all()
        return PaginatedResult(
            items=[LetterResponseDTO.from_entity(item) for item in items],
            total=total,
            offset=offset,
            limit=limit,
        )
