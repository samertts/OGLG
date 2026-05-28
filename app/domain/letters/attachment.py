from __future__ import annotations

import hashlib
import os
import uuid
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Attachment:
    id: str
    letter_id: str
    filename: str
    original_name: str
    mime_type: str
    file_size: int
    extension: str
    sha256_hash: str
    storage_path: str
    uploaded_at: datetime
    uploaded_by: str
    description: str = ""
    is_encrypted: bool = False

    @staticmethod
    def create(
        letter_id: str,
        filepath: str,
        original_name: str,
        uploaded_by: str,
        description: str = "",
    ) -> Attachment:
        file_size = os.path.getsize(filepath)
        ext = os.path.splitext(original_name)[1].lower()
        sha256_hash = hashlib.sha256()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                sha256_hash.update(chunk)
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
        return Attachment(
            id=str(uuid.uuid4()),
            letter_id=letter_id,
            filename=f"{uuid.uuid4().hex}{ext}",
            original_name=original_name,
            mime_type=mime_type,
            file_size=file_size,
            extension=ext,
            sha256_hash=sha256_hash.hexdigest(),
            storage_path="",
            uploaded_at=datetime.now(),
            uploaded_by=uploaded_by,
            description=description,
        )

    @property
    def size_display(self) -> str:
        if self.file_size < 1024:
            return f"{self.file_size} B"
        elif self.file_size < 1024 * 1024:
            return f"{self.file_size / 1024:.1f} KB"
        else:
            return f"{self.file_size / (1024 * 1024):.1f} MB"

    @property
    def is_pdf(self) -> bool:
        return self.mime_type == "application/pdf"

    @property
    def is_image(self) -> bool:
        return self.mime_type.startswith("image/")

    @property
    def is_document(self) -> bool:
        return self.mime_type in (
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )

    @property
    def is_spreadsheet(self) -> bool:
        return self.mime_type in (
            "application/vnd.ms-excel",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
