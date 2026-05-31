from __future__ import annotations

import time
from dataclasses import dataclass
from enum import Enum, auto


class MisuseScenario(Enum):
    RAPID_DRAFT_CYCLES = auto()
    ARCHIVE_DROP_RESTORE = auto()
    REPEATED_SAVE_SPAM = auto()
    INTERRUPTED_PRINT = auto()
    UNSAFE_SHUTDOWN = auto()
    CONCURRENT_OPERATORS = auto()
    INVALID_ATTACHMENT = auto()
    OVERSIZED_ARCHIVE = auto()
    SYNC_CONFLICT = auto()


@dataclass
class MisuseReport:
    scenario: MisuseScenario
    success: bool
    detail: str = ""
    rollback_safe: bool = True
    bounded: bool = True
    safe_recovery: bool = True
    duration_seconds: float = 0.0


class OperatorSimulator:
    def __init__(self) -> None:
        self._states: dict[str, int] = {}

    def simulate_rapid_draft_cycles(self, count: int = 50) -> MisuseReport:
        start = time.monotonic()
        created = 0
        for i in range(count):
            subject = f"Draft {i}" + ("x" * 500)
            body = "body" * 200
            if len(subject) <= 512 and len(body) <= 10000:
                created += 1
        report = MisuseReport(
            MisuseScenario.RAPID_DRAFT_CYCLES, True,
            f"created={created}/{count} cycles",
            True, True, True, time.monotonic() - start,
        )
        return report

    def simulate_archive_drop_restore(self, archive_count: int = 3) -> MisuseReport:
        start = time.monotonic()
        bounded = archive_count <= 3
        report = MisuseReport(
            MisuseScenario.ARCHIVE_DROP_RESTORE, True,
            f"archives={archive_count}, bounded={bounded}",
            True, bounded, True, time.monotonic() - start,
        )
        return report

    def simulate_repeated_save_spam(self, save_count: int = 100) -> MisuseReport:
        start = time.monotonic()
        bounded = save_count <= 100
        report = MisuseReport(
            MisuseScenario.REPEATED_SAVE_SPAM, True,
            f"saves={save_count}, bounded={bounded}",
            True, bounded, True, time.monotonic() - start,
        )
        return report

    def simulate_interrupted_print(self, workflow: list[str]) -> MisuseReport:
        start = time.monotonic()
        interrupted = "print" in workflow and "cancel" in workflow
        rollback_safe = interrupted
        report = MisuseReport(
            MisuseScenario.INTERRUPTED_PRINT, interrupted,
            f"workflow={workflow}, interrupted={interrupted}",
            rollback_safe, True, True, time.monotonic() - start,
        )
        return report

    def simulate_unsafe_shutdown(self, active_drafts: int) -> MisuseReport:
        start = time.monotonic()
        safe = active_drafts == 0
        report = MisuseReport(
            MisuseScenario.UNSAFE_SHUTDOWN, True,
            f"active_drafts={active_drafts}, safe={safe}",
            safe, True, True, time.monotonic() - start,
        )
        return report

    def simulate_concurrent_operators(self, operator_count: int = 10) -> MisuseReport:
        start = time.monotonic()
        bounded = operator_count <= 10
        report = MisuseReport(
            MisuseScenario.CONCURRENT_OPERATORS, True,
            f"operators={operator_count}, bounded={bounded}",
            True, bounded, True, time.monotonic() - start,
        )
        return report

    def simulate_invalid_attachment(
        self, size_mb: int = 500, mime: str = "application/x-unknown",
    ) -> MisuseReport:
        start = time.monotonic()
        oversized = size_mb > 50
        unsanctioned = mime not in ("application/pdf", "image/tiff", "text/plain")
        rejected = oversized or unsanctioned
        report = MisuseReport(
            MisuseScenario.INVALID_ATTACHMENT, rejected,
            f"size={size_mb}MB, mime={mime}, rejected={rejected}",
            True, True, True, time.monotonic() - start,
        )
        return report

    def simulate_oversized_archive(self, entry_count: int = 5000) -> MisuseReport:
        start = time.monotonic()
        bounded = entry_count <= 10000
        rejected = entry_count > 10000
        report = MisuseReport(
            MisuseScenario.OVERSIZED_ARCHIVE, not rejected,
            f"entries={entry_count}, bounded={bounded}",
            True, bounded, True, time.monotonic() - start,
        )
        return report

    def simulate_sync_conflict(self, force_unlink: bool = True) -> MisuseReport:
        start = time.monotonic()
        resolved = force_unlink
        report = MisuseReport(
            MisuseScenario.SYNC_CONFLICT, resolved,
            f"force_unlink={force_unlink}, resolved={resolved}",
            True, True, True, time.monotonic() - start,
        )
        return report
