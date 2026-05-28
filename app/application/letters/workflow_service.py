from __future__ import annotations

from datetime import datetime
from typing import Any

from loguru import logger

from app.application.letters.dto import (
    ArchiveLetterDTO,
    CreateLetterDTO,
    EditLetterDTO,
    LetterResultDTO,
    ReviewLetterDTO,
)
from app.application.letters.numbering_engine import NumberingEngine
from app.application.letters.validation_service import LetterValidationService
from app.domain.letters.aggregate import LetterAggregate
from app.domain.letters.enums import (
    LetterStatus,
)
from app.domain.letters.events import DomainEvent
from app.domain.letters.interfaces import (
    AttachmentRepository,
    AuditRepository,
    LetterRepository,
)
from app.domain.letters.value_objects import (
    Attachment,
)


class WorkflowService:
    def __init__(
        self,
        letter_repo: LetterRepository,
        audit_repo: AuditRepository,
        attachment_repo: AttachmentRepository,
        numbering_engine: NumberingEngine,
        validation_service: LetterValidationService,
        uow_factory: Any,
        attachment_storage: Any,
    ) -> None:
        self._letter_repo = letter_repo
        self._audit_repo = audit_repo
        self._attachment_repo = attachment_repo
        self._numbering = numbering_engine
        self._validator = validation_service
        self._uow_factory = uow_factory
        self._attachment_storage = attachment_storage

    def create_draft(self, dto: CreateLetterDTO) -> LetterResultDTO:
        vr = self._validator.validate_create(
            dto.letter_type, dto.subject, dto.body,
            dto.sender_id, dto.sender_name, dto.sender_department,
            dto.department_id, dto.created_by_id,
        )
        vr.raise_if_invalid()

        letter = LetterAggregate.create(
            letter_type=dto.letter_type,
            subject=dto.subject,
            body=dto.body,
            sender_id=dto.sender_id,
            sender_name=dto.sender_name,
            sender_department=dto.sender_department,
            department_id=dto.department_id,
            created_by_id=dto.created_by_id,
            priority=dto.priority,
            classification=dto.classification,
            language=dto.language,
            recipient_name=dto.recipient_name,
            recipient_department=dto.recipient_department,
            recipient_address=dto.recipient_address,
            recipient_id=dto.recipient_id,
            reference_number=dto.reference_number,
        )

        with self._uow_factory() as uow:
            self._letter_repo.save(letter)
            for event in letter.pop_events():
                self._audit_repo.append(event)
            uow.commit()

        logger.info(f"Letter draft created: {letter.id}")
        return LetterResultDTO.from_aggregate(letter)

    def edit_draft(self, dto: EditLetterDTO) -> LetterResultDTO:
        letter = self._letter_repo.get_by_id(dto.letter_id)
        if letter is None:
            raise ValueError(f"Letter not found: {dto.letter_id}")

        ve = self._validator.validate_edit(letter.status)
        ve.raise_if_invalid()

        letter.edit(
            user_id=dto.user_id,
            subject=dto.subject,
            body=dto.body,
            priority=dto.priority,
            classification=dto.classification,
            recipient_name=dto.recipient_name,
            recipient_department=dto.recipient_department,
            recipient_address=dto.recipient_address,
        )

        with self._uow_factory() as uow:
            self._letter_repo.save(letter)
            for event in letter.pop_events():
                self._audit_repo.append(event)
            uow.commit()

        logger.info(f"Letter edited: {letter.id}")
        return LetterResultDTO.from_aggregate(letter)

    def submit_for_review(self, letter_id: str, user_id: str) -> LetterResultDTO:
        letter = self._letter_repo.get_by_id(letter_id)
        if letter is None:
            raise ValueError(f"Letter not found: {letter_id}")

        letter.submit_for_review(user_id)

        with self._uow_factory() as uow:
            self._letter_repo.save(letter)
            for event in letter.pop_events():
                self._audit_repo.append(event)
            uow.commit()

        logger.info(f"Letter submitted for review: {letter_id}")
        return LetterResultDTO.from_aggregate(letter)

    def start_review(self, letter_id: str, user_id: str) -> LetterResultDTO:
        letter = self._letter_repo.get_by_id(letter_id)
        if letter is None:
            raise ValueError(f"Letter not found: {letter_id}")
        letter.start_review(user_id)
        with self._uow_factory() as uow:
            self._letter_repo.save(letter)
            for event in letter.pop_events():
                self._audit_repo.append(event)
            uow.commit()
        logger.info(f"Review started for letter: {letter_id}")
        return LetterResultDTO.from_aggregate(letter)

    def approve(self, dto: ReviewLetterDTO) -> LetterResultDTO:
        letter = self._letter_repo.get_by_id(dto.letter_id)
        if letter is None:
            raise ValueError(f"Letter not found: {dto.letter_id}")

        number_result = self._numbering.generate(letter.department_id)
        letter.assign_number(number_result, dto.user_id)
        letter.approve(dto.user_id, dto.reviewer_id, dto.notes)

        with self._uow_factory() as uow:
            self._letter_repo.save(letter)
            for event in letter.pop_events():
                self._audit_repo.append(event)
            uow.commit()

        logger.info(f"Letter approved: {dto.letter_id}, number: {letter.number}")
        return LetterResultDTO.from_aggregate(letter)

    def approve_with_number(self, dto: ReviewLetterDTO, number: str) -> LetterResultDTO:
        letter = self._letter_repo.get_by_id(dto.letter_id)
        if letter is None:
            raise ValueError(f"Letter not found: {dto.letter_id}")

        letter.assign_number(number, dto.user_id)
        letter.approve(dto.user_id, dto.reviewer_id, dto.notes)

        with self._uow_factory() as uow:
            self._letter_repo.save(letter)
            for event in letter.pop_events():
                self._audit_repo.append(event)
            uow.commit()

        logger.info(f"Letter approved with number: {dto.letter_id}, number: {number}")
        return LetterResultDTO.from_aggregate(letter)

    def reject(self, dto: ReviewLetterDTO) -> LetterResultDTO:
        letter = self._letter_repo.get_by_id(dto.letter_id)
        if letter is None:
            raise ValueError(f"Letter not found: {dto.letter_id}")
        if not dto.reason:
            raise ValueError("Rejection reason is required")

        letter.reject(dto.user_id, dto.reviewer_id, dto.reason)

        with self._uow_factory() as uow:
            self._letter_repo.save(letter)
            for event in letter.pop_events():
                self._audit_repo.append(event)
            uow.commit()

        logger.info(f"Letter rejected: {dto.letter_id}")
        return LetterResultDTO.from_aggregate(letter)

    def return_to_draft(self, letter_id: str, user_id: str) -> LetterResultDTO:
        letter = self._letter_repo.get_by_id(letter_id)
        if letter is None:
            raise ValueError(f"Letter not found: {letter_id}")
        letter.return_to_draft(user_id)
        with self._uow_factory() as uow:
            self._letter_repo.save(letter)
            for event in letter.pop_events():
                self._audit_repo.append(event)
            uow.commit()
        logger.info(f"Letter returned to draft: {letter_id}")
        return LetterResultDTO.from_aggregate(letter)

    def archive(self, dto: ArchiveLetterDTO) -> LetterResultDTO:
        letter = self._letter_repo.get_by_id(dto.letter_id)
        if letter is None:
            raise ValueError(f"Letter not found: {dto.letter_id}")

        letter.archive(dto.user_id, dto.reason)

        with self._uow_factory() as uow:
            self._letter_repo.save(letter)
            for event in letter.pop_events():
                self._audit_repo.append(event)
            uow.commit()

        logger.info(f"Letter archived: {dto.letter_id}")
        return LetterResultDTO.from_aggregate(letter)

    def restore(self, dto: ArchiveLetterDTO) -> LetterResultDTO:
        letter = self._letter_repo.get_by_id(dto.letter_id)
        if letter is None:
            raise ValueError(f"Letter not found: {dto.letter_id}")

        letter.restore(dto.user_id, dto.reason)

        with self._uow_factory() as uow:
            self._letter_repo.save(letter)
            for event in letter.pop_events():
                self._audit_repo.append(event)
            uow.commit()

        logger.info(f"Letter restored: {dto.letter_id}")
        return LetterResultDTO.from_aggregate(letter)

    def soft_delete(self, dto: ArchiveLetterDTO) -> LetterResultDTO:
        letter = self._letter_repo.get_by_id(dto.letter_id)
        if letter is None:
            raise ValueError(f"Letter not found: {dto.letter_id}")

        letter.soft_delete(dto.user_id, dto.reason)

        with self._uow_factory() as uow:
            self._letter_repo.save(letter)
            for event in letter.pop_events():
                self._audit_repo.append(event)
            uow.commit()

        logger.info(f"Letter soft deleted: {dto.letter_id}")
        return LetterResultDTO.from_aggregate(letter)

    def register_incoming(self, dto: CreateLetterDTO) -> LetterResultDTO:
        result = self.create_draft(dto)
        letter = self._letter_repo.get_by_id(result.id)
        if letter is None:
            raise RuntimeError("Failed to create incoming letter")
        letter.mark_received(dto.created_by_id)
        number = self._numbering.generate(letter.department_id)
        letter.assign_number(number, dto.created_by_id)
        with self._uow_factory() as uow:
            self._letter_repo.save(letter)
            for event in letter.pop_events():
                self._audit_repo.append(event)
            uow.commit()
        logger.info(f"Incoming letter registered: {letter.id}, number: {number}")
        return LetterResultDTO.from_aggregate(letter)

    def mark_sent(self, letter_id: str, user_id: str) -> LetterResultDTO:
        letter = self._letter_repo.get_by_id(letter_id)
        if letter is None:
            raise ValueError(f"Letter not found: {letter_id}")
        letter.mark_sent(user_id)
        with self._uow_factory() as uow:
            self._letter_repo.save(letter)
            for event in letter.pop_events():
                self._audit_repo.append(event)
            uow.commit()
        logger.info(f"Letter marked sent: {letter_id}")
        return LetterResultDTO.from_aggregate(letter)

    def mark_delivered(self, letter_id: str, user_id: str, proof: str | None = None) -> LetterResultDTO:
        letter = self._letter_repo.get_by_id(letter_id)
        if letter is None:
            raise ValueError(f"Letter not found: {letter_id}")
        letter.mark_delivered(user_id, proof)
        with self._uow_factory() as uow:
            self._letter_repo.save(letter)
            for event in letter.pop_events():
                self._audit_repo.append(event)
            uow.commit()
        logger.info(f"Letter marked delivered: {letter_id}")
        return LetterResultDTO.from_aggregate(letter)

    def get_letter(self, letter_id: str) -> LetterResultDTO | None:
        letter = self._letter_repo.get_by_id(letter_id)
        if letter is None:
            return None
        return LetterResultDTO.from_aggregate(letter)

    def list_by_department(self, department_id: str, offset: int = 0, limit: int = 50) -> list[LetterResultDTO]:
        letters = self._letter_repo.list_by_department(department_id, offset, limit)
        return [LetterResultDTO.from_aggregate(item) for item in letters]

    def list_by_status(self, status: LetterStatus, offset: int = 0, limit: int = 50) -> list[LetterResultDTO]:
        letters = self._letter_repo.list_by_status(status, offset, limit)
        return [LetterResultDTO.from_aggregate(item) for item in letters]

    def add_attachment(self, letter_id: str, filepath: str, original_name: str, uploaded_by: str, description: str = "") -> dict[str, Any]:
        import hashlib
        import os
        import uuid

        letter = self._letter_repo.get_by_id(letter_id)
        if letter is None:
            raise ValueError(f"Letter not found: {letter_id}")

        file_size = os.path.getsize(filepath)
        ext = os.path.splitext(original_name)[1].lower()
        mime_map = {
            ".pdf": "application/pdf",
            ".doc": "application/msword",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".xls": "application/vnd.ms-excel",
            ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".tiff": "image/tiff",
            ".zip": "application/zip",
        }
        mime_type = mime_map.get(ext, "application/octet-stream")

        vr = self._validator.validate_attachment(original_name, file_size, mime_type)
        vr.raise_if_invalid()

        sha256_hash = hashlib.sha256()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                sha256_hash.update(chunk)
        file_hash = sha256_hash.hexdigest()

        existing = self._attachment_repo.get_by_hash(file_hash)
        if existing is not None:
            raise ValueError(f"Duplicate attachment detected (same content as {existing.original_name})")

        safe_name = f"{uuid.uuid4().hex}{ext}"
        storage_path = self._attachment_storage.store(filepath, safe_name, letter_id)

        attachment = Attachment(
            id=str(uuid.uuid4()),
            filename=safe_name,
            original_name=original_name,
            mime_type=mime_type,
            file_size=file_size,
            extension=ext,
            sha256_hash=file_hash,
            storage_path=storage_path,
            uploaded_at=datetime.now(),
            uploaded_by=uploaded_by,
            description=description,
        )
        letter.add_attachment(attachment)

        with self._uow_factory() as uow:
            self._letter_repo.save(letter)
            self._attachment_repo.save(attachment)
            uow.commit()

        logger.info(f"Attachment added to letter {letter_id}: {original_name}")
        return {
            "attachment_id": attachment.id,
            "filename": safe_name,
            "original_name": original_name,
            "file_size": file_size,
            "sha256_hash": file_hash,
            "mime_type": mime_type,
        }

    def record_print(self, letter_id: str, user_id: str, copies: int = 1) -> None:
        letter = self._letter_repo.get_by_id(letter_id)
        if letter is None:
            raise ValueError(f"Letter not found: {letter_id}")
        letter.record_print(user_id, copies)
        with self._uow_factory() as uow:
            self._letter_repo.save(letter)
            for event in letter.pop_events():
                self._audit_repo.append(event)
            uow.commit()
        logger.info(f"Print recorded for letter {letter_id}, copies: {copies}")

    def get_events(self, letter_id: str) -> list[DomainEvent]:
        return self._audit_repo.get_events_for_letter(letter_id)
