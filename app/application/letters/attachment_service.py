from __future__ import annotations

import hashlib
import os
import uuid
from datetime import datetime
from typing import Any, Protocol

from loguru import logger

from app.domain.letters.interfaces import AttachmentRepository
from app.domain.letters.value_objects import Attachment


class AttachmentStorage(Protocol):
    def store(self, source_path: str, safe_name: str, letter_id: str) -> str: ...
    def retrieve(self, storage_path: str) -> str: ...
    def delete(self, storage_path: str) -> None: ...
    def get_full_path(self, storage_path: str) -> str: ...


class AttachmentService:
    ALLOWED_EXTENSIONS = {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".jpg", ".jpeg", ".png", ".tiff", ".zip"}
    MAX_FILE_SIZE = 50 * 1024 * 1024
    MAX_ATTACHMENTS_PER_LETTER = 20
    MIME_MAP = {
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

    def __init__(self, attachment_repo: AttachmentRepository, storage: AttachmentStorage) -> None:
        self._repo = attachment_repo
        self._storage = storage

    def register(self, letter_id: str, filepath: str, original_name: str, uploaded_by: str, description: str = "") -> dict[str, Any]:
        file_size = os.path.getsize(filepath)
        ext = os.path.splitext(original_name)[1].lower()
        mime_type = self.MIME_MAP.get(ext, "application/octet-stream")

        if ext not in self.ALLOWED_EXTENSIONS:
            raise ValueError(f"Extension '{ext}' not allowed")
        if file_size <= 0:
            raise ValueError("File size must be greater than 0")
        if file_size > self.MAX_FILE_SIZE:
            raise ValueError(f"File exceeds {self.MAX_FILE_SIZE // (1024 * 1024)}MB limit")

        sha256_hash = hashlib.sha256()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                sha256_hash.update(chunk)
        file_hash = sha256_hash.hexdigest()

        existing = self._repo.get_by_hash(file_hash)
        if existing is not None:
            raise ValueError(f"Duplicate content: matches {existing.original_name}")

        safe_name = f"{uuid.uuid4().hex}{ext}"
        storage_path = self._storage.store(filepath, safe_name, letter_id)

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
        self._repo.save(attachment)
        logger.info(f"Attachment registered: {attachment.id} - {original_name}")
        return {
            "attachment_id": attachment.id,
            "filename": safe_name,
            "original_name": original_name,
            "file_size": file_size,
            "sha256_hash": file_hash,
            "mime_type": mime_type,
            "storage_path": storage_path,
        }

    def get_by_id(self, attachment_id: str) -> Attachment | None:
        return self._repo.get_by_id(attachment_id)

    def list_by_letter(self, letter_id: str) -> list[Attachment]:
        return self._repo.list_by_letter(letter_id)

    def delete(self, attachment_id: str) -> None:
        attachment = self._repo.get_by_id(attachment_id)
        if attachment is None:
            raise ValueError(f"Attachment not found: {attachment_id}")
        self._storage.delete(attachment.storage_path)
        self._repo.delete(attachment_id)
        logger.info(f"Attachment deleted: {attachment_id}")

    def get_file_path(self, attachment_id: str) -> str:
        attachment = self._repo.get_by_id(attachment_id)
        if attachment is None:
            raise ValueError(f"Attachment not found: {attachment_id}")
        return self._storage.get_full_path(attachment.storage_path)

    def detect_duplicate(self, filepath: str) -> str | None:
        sha256_hash = hashlib.sha256()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                sha256_hash.update(chunk)
        file_hash = sha256_hash.hexdigest()
        existing = self._repo.get_by_hash(file_hash)
        if existing is not None:
            return existing.original_name
        return None
