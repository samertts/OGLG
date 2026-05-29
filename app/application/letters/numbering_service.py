from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from app.application.letters.numbering_context import NumberingContext
from app.application.letters.numbering_policy import (
    format_number,
    normalize_sequence,
    parse_number,
    validate_number_format,
    validate_prefix,
    validate_year,
)
from app.application.letters.numbering_result import NumberingResult
from app.application.letters.numbering_sequence import NumberingSequence
from app.application.letters.sqlite_numbering_repository import (
    SqliteNumberingRepository,
)

_RETRY_DELAY = 0.05
_MAX_RETRIES = 5


class NumberingServiceError(Exception):
    pass


@dataclass
class NumberingIntegrityReport:
    total_sequences: int = 0
    total_allocations: int = 0
    corrupted_sequences: list[dict[str, Any]] = field(default_factory=list)
    gaps_detected: list[dict[str, Any]] = field(default_factory=list)
    orphans_detected: list[dict[str, Any]] = field(default_factory=list)
    consistency_issues: list[dict[str, Any]] = field(default_factory=list)
    is_healthy: bool = True


class NumberingService:
    def __init__(self, repo: SqliteNumberingRepository) -> None:
        self._repo = repo

    def allocate(
        self,
        context: NumberingContext,
        metadata: dict[str, Any] | None = None,
    ) -> NumberingResult:
        prefix = context.department_code
        year = context.effective_year
        return self._allocate_with_retry(prefix, year, 1, metadata)

    def allocate_batch(
        self,
        context: NumberingContext,
        count: int,
        metadata: dict[str, Any] | None = None,
    ) -> NumberingResult:
        prefix = context.department_code
        year = context.effective_year

        if count < 1:
            return NumberingResult.fail(
                "count must be at least 1", error_code="INVALID_COUNT"
            )
        if count > 1000:
            return NumberingResult.fail(
                "count cannot exceed 1000", error_code="BATCH_TOO_LARGE"
            )

        return self._allocate_with_retry(prefix, year, count, metadata)

    def _allocate_with_retry(
        self,
        prefix: str,
        year: int,
        count: int,
        metadata: dict[str, Any] | None,
    ) -> NumberingResult:
        prefix_err = validate_prefix(prefix)
        if prefix_err:
            return NumberingResult.fail(prefix_err, error_code="INVALID_PREFIX")

        year_err = validate_year(year)
        if year_err:
            return NumberingResult.fail(year_err, error_code="INVALID_YEAR")

        for attempt in range(_MAX_RETRIES):
            try:
                return self._repo.allocate_number(prefix, year, count, metadata)
            except OperationalError as exc:
                if "database is locked" in str(exc) and attempt < _MAX_RETRIES - 1:
                    time.sleep(_RETRY_DELAY * (attempt + 1))
                    continue
                return NumberingResult.fail(
                    str(exc), error_code="BUSY_TIMEOUT"
                )
            except Exception as exc:
                return NumberingResult.fail(
                    str(exc), error_code="ALLOCATION_FAILED"
                )

        return NumberingResult.fail(
            "allocation failed after retries", error_code="RETRY_EXHAUSTED"
        )

    def get_sequence_info(
        self, context: NumberingContext
    ) -> NumberingSequence | None:
        return self._repo.get_current_sequence(
            context.department_code, context.effective_year
        )

    def sequence_exists(self, context: NumberingContext) -> bool:
        return self._repo.sequence_exists(
            context.department_code, context.effective_year
        )

    def reset_sequence(
        self, context: NumberingContext, value: int = 0
    ) -> NumberingResult:
        self._repo.reset_sequence(
            context.department_code, context.effective_year, value
        )
        return NumberingResult.ok(
            number="",
            prefix=context.department_code,
            year=context.effective_year,
            sequence=value,
            metadata={"reset": True},
        )

    def list_sequences(self) -> list[NumberingSequence]:
        return self._repo.list_sequences()

    def get_allocation_history(
        self, prefix: str, year: int
    ) -> list[dict[str, Any]]:
        return self._repo.get_allocation_history(prefix, year)

    def run_integrity_check(self) -> NumberingIntegrityReport:
        report = NumberingIntegrityReport()

        sequences = self._repo.list_sequences()
        report.total_sequences = len(sequences)

        for seq in sequences:
            history = self._repo.get_allocation_history(seq.prefix, seq.year)
            report.total_allocations += len(history)

            hist_records = self._repo.get_allocation_history(seq.prefix, seq.year)
            gaps = _detect_gaps(hist_records, seq.last_sequence)
            for g in gaps:
                report.gaps_detected.append({"prefix": seq.prefix, "year": seq.year, "gap": g})
                report.is_healthy = False

        orphans = self._repo.detect_orphans()
        for o in orphans:
            report.orphans_detected.append(o)
            report.is_healthy = False

        consistency = self._repo.verify_sequence_consistency()
        if not consistency.get("consistent", True):
            for issue in consistency.get("issues", []):
                report.consistency_issues.append(issue)
                report.is_healthy = False

        return report

    def validate_number(self, number: str) -> bool:
        return validate_number_format(number)

    def parse_number(self, number: str) -> tuple[str, int, int]:
        return parse_number(number)

    def format_number(self, prefix: str, year: int, sequence: int) -> str:
        return format_number(prefix, year, sequence)

    def detect_orphans(self) -> list[dict[str, Any]]:
        return self._repo.detect_orphans()

    def verify_sequence_consistency(self) -> dict[str, Any]:
        return self._repo.verify_sequence_consistency()


def _detect_gaps(
    history: list[dict[str, Any]], last_sequence: int
) -> list[dict[str, Any]]:
    gaps: list[dict[str, Any]] = []
    if not history:
        return gaps

    allocated = sorted(
        h.get("sequence", h.get("allocated_sequence", 0)) for h in history
    )
    if not allocated:
        return gaps

    expected = list(range(1, len(allocated) + 1))
    if allocated != expected:
        gaps.append({
            "expected_range": f"1-{len(allocated)}",
            "actual_range": f"{allocated[0]}-{allocated[-1]}",
            "expected_count": len(expected),
            "actual_count": len(allocated),
        })

    max_allocated = max(allocated)
    if max_allocated != last_sequence:
        gaps.append({
            "type": "sequence_mismatch",
            "history_max": max_allocated,
            "sequence_table": last_sequence,
        })

    return gaps


__all__ = [
    "NumberingService",
    "NumberingServiceError",
    "NumberingIntegrityReport",
]
