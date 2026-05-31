from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from typing import Any


class PdfGenerationState(Enum):
    IDLE = auto()
    GENERATING = auto()
    COMPLETED = auto()
    FAILED = auto()
    CANCELLED = auto()


@dataclass
class PdfJob:
    job_id: str
    document_id: str
    state: PdfGenerationState = PdfGenerationState.IDLE
    page_count: int = 0
    size_bytes: int = 0
    error_message: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_terminal(self) -> bool:
        return self.state in (
            PdfGenerationState.COMPLETED,
            PdfGenerationState.FAILED,
            PdfGenerationState.CANCELLED,
        )

    @property
    def is_success(self) -> bool:
        return self.state == PdfGenerationState.COMPLETED


@dataclass
class PrintJobResult:
    job: PdfJob
    preview_snippet: str = ""
    pages: list[int] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return self.job.is_success


class PdfJobManager:
    MAX_JOBS = 100
    MAX_PAGES = 500
    MAX_SIZE_BYTES = 50 * 1024 * 1024

    def __init__(self) -> None:
        self._jobs: dict[str, PdfJob] = {}

    @property
    def job_count(self) -> int:
        return len(self._jobs)

    @property
    def job_ids(self) -> list[str]:
        return list(self._jobs.keys())

    def create_job(self, job_id: str, document_id: str) -> PdfJob | None:
        if len(self._jobs) >= self.MAX_JOBS:
            return None
        job = PdfJob(job_id=job_id, document_id=document_id)
        self._jobs[job_id] = job
        return job

    def get_job(self, job_id: str) -> PdfJob | None:
        return self._jobs.get(job_id)

    def complete_job(self, job_id: str, page_count: int, size_bytes: int) -> bool:
        job = self._jobs.get(job_id)
        if job is None:
            return False
        if size_bytes > self.MAX_SIZE_BYTES:
            job.state = PdfGenerationState.FAILED
            job.error_message = f"PDF exceeds {self.MAX_SIZE_BYTES} byte limit"
            return True
        job.state = PdfGenerationState.COMPLETED
        job.page_count = page_count
        job.size_bytes = size_bytes
        job.completed_at = datetime.now(timezone.utc)
        return True

    def fail_job(self, job_id: str, error: str) -> bool:
        job = self._jobs.get(job_id)
        if job is None:
            return False
        job.state = PdfGenerationState.FAILED
        job.error_message = error
        return True

    def cancel_job(self, job_id: str) -> bool:
        job = self._jobs.get(job_id)
        if job is None or job.is_terminal:
            return False
        job.state = PdfGenerationState.CANCELLED
        return True

    def clean_old_jobs(self, max_age_seconds: float = 3600) -> int:
        now = datetime.now(timezone.utc)
        removed = 0
        to_remove: list[str] = []
        for job_id, job in self._jobs.items():
            if job.is_terminal and job.completed_at:
                age = (now - job.completed_at).total_seconds()
                if age > max_age_seconds:
                    to_remove.append(job_id)
        for job_id in to_remove:
            del self._jobs[job_id]
            removed += 1
        return removed

    def clear(self) -> None:
        self._jobs.clear()
