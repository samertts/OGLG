from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from typing import Any


class LetterState(Enum):
    DRAFT = auto()
    PENDING_APPROVAL = auto()
    APPROVED = auto()
    REJECTED = auto()
    ARCHIVED = auto()


class WorkflowActionType(Enum):
    CREATE = auto()
    SAVE_DRAFT = auto()
    SUBMIT = auto()
    APPROVE = auto()
    REJECT = auto()
    ARCHIVE = auto()
    ATTACH = auto()
    DETACH = auto()


@dataclass
class WorkflowAction:
    action_id: str
    action_type: WorkflowActionType
    letter_id: str
    user_id: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    audit_token: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CorrespondenceDraft:
    letter_id: str
    subject: str = ""
    body: str = ""
    sender: str = ""
    recipient: str = ""
    classification: str = "unclassified"
    reference_number: str | None = None
    state: LetterState = LetterState.DRAFT
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    has_unsaved_changes: bool = False
    version: int = 1

    def mark_saved(self) -> None:
        self.has_unsaved_changes = False
        self.updated_at = datetime.now(timezone.utc)
        self.version += 1

    def mark_dirty(self) -> None:
        self.has_unsaved_changes = True
        self.updated_at = datetime.now(timezone.utc)


class DraftManager:
    MAX_DRAFTS = 50
    MAX_SUBJECT_LENGTH = 500
    MAX_BODY_LENGTH = 100_000

    def __init__(self) -> None:
        self._drafts: dict[str, CorrespondenceDraft] = {}
        self._action_log: list[WorkflowAction] = []

    @property
    def draft_count(self) -> int:
        return len(self._drafts)

    @property
    def draft_ids(self) -> list[str]:
        return list(self._drafts.keys())

    def create_draft(
        self, letter_id: str, subject: str = "", body: str = "",
        sender: str = "", recipient: str = "",
    ) -> CorrespondenceDraft:
        if len(self._drafts) >= self.MAX_DRAFTS:
            raise RuntimeError(f"Max drafts ({self.MAX_DRAFTS}) reached")
        if len(subject) > self.MAX_SUBJECT_LENGTH:
            raise ValueError(f"Subject exceeds {self.MAX_SUBJECT_LENGTH} chars")
        if len(body) > self.MAX_BODY_LENGTH:
            raise ValueError(f"Body exceeds {self.MAX_BODY_LENGTH} chars")
        draft = CorrespondenceDraft(
            letter_id=letter_id, subject=subject, body=body,
            sender=sender, recipient=recipient,
        )
        self._drafts[letter_id] = draft
        self._log_action(WorkflowActionType.CREATE, letter_id, "")
        return draft

    def get_draft(self, letter_id: str) -> CorrespondenceDraft | None:
        return self._drafts.get(letter_id)

    def update_draft(self, letter_id: str, **kwargs: Any) -> CorrespondenceDraft | None:
        draft = self._drafts.get(letter_id)
        if draft is None:
            return None
        for key, value in kwargs.items():
            allowed = (
                "subject", "body", "sender", "recipient",
                "classification", "reference_number",
            )
            if hasattr(draft, key) and key in allowed:
                if key == "subject" and len(value) > self.MAX_SUBJECT_LENGTH:
                    raise ValueError(f"Subject exceeds {self.MAX_SUBJECT_LENGTH} chars")
                if key == "body" and len(value) > self.MAX_BODY_LENGTH:
                    raise ValueError(f"Body exceeds {self.MAX_BODY_LENGTH} chars")
                setattr(draft, key, value)
        draft.mark_dirty()
        self._log_action(WorkflowActionType.SAVE_DRAFT, letter_id, "")
        return draft

    def delete_draft(self, letter_id: str) -> bool:
        if letter_id in self._drafts:
            del self._drafts[letter_id]
            return True
        return False

    def submit_for_approval(self, letter_id: str, user_id: str) -> CorrespondenceDraft | None:
        draft = self._drafts.get(letter_id)
        if draft is None:
            return None
        if draft.state != LetterState.DRAFT:
            return None
        draft.state = LetterState.PENDING_APPROVAL
        draft.mark_saved()
        self._log_action(WorkflowActionType.SUBMIT, letter_id, user_id)
        return draft

    def _log_action(self, action_type: WorkflowActionType, letter_id: str, user_id: str) -> None:
        action = WorkflowAction(
            action_id=f"{action_type.name}_{letter_id}_{datetime.now(timezone.utc).timestamp()}",
            action_type=action_type, letter_id=letter_id, user_id=user_id,
        )
        self._action_log.append(action)

    @property
    def action_log(self) -> list[WorkflowAction]:
        return list(self._action_log)

    def clear(self) -> None:
        self._drafts.clear()
        self._action_log.clear()


@dataclass
class NumberingPreview:
    prefix: str = ""
    sequence: int = 0
    year: int = 0
    full_number: str = ""
    formatted: str = ""

    def generate(self, prefix: str, sequence: int, year: int | None = None) -> None:
        self.prefix = prefix
        self.sequence = sequence
        self.year = year or datetime.now(timezone.utc).year
        self.full_number = f"{prefix}-{self.year}-{sequence:04d}"
        self.formatted = f"{prefix} / {sequence:04d} / {self.year}"
