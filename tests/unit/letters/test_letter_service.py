from __future__ import annotations

import pytest

from app.application.letters.letter_service import (
    LetterNotFoundError,
    LetterNotEditableError,
    LetterService,
    LetterServiceError,
)
from app.domain.letters.letter import LetterType
from app.domain.letters.letter_status import LetterStatus
from app.domain.letters.letter_priority import LetterPriority
from app.domain.letters.letter_classification import LetterClassification
from tests.unit.letters.test_services_common import (
    InMemoryAuditRepo,
    InMemoryLetterRepo,
    InMemoryUoW,
)


@pytest.fixture
def letter_repo() -> InMemoryLetterRepo:
    return InMemoryLetterRepo()


@pytest.fixture
def audit_repo() -> InMemoryAuditRepo:
    return InMemoryAuditRepo()


@pytest.fixture
def service(letter_repo: InMemoryLetterRepo, audit_repo: InMemoryAuditRepo) -> LetterService:
    return LetterService(letter_repo, audit_repo, lambda: InMemoryUoW())


class TestCreateDraft:
    def test_create_outgoing(self, service: LetterService, letter_repo: InMemoryLetterRepo) -> None:
        letter = service.create_draft(
            letter_type=LetterType.OUTGOING.value,
            subject="Official Letter",
            body="Body content",
            sender_id="user-1",
            sender_name="Ali",
            sender_department="MOH",
            department_id="dept-1",
            created_by_id="user-1",
            recipient_name="MoF",
            recipient_department="Finance",
        )
        assert letter.id is not None
        assert letter.status == LetterStatus.DRAFT
        assert letter.letter_type == LetterType.OUTGOING.value
        saved = letter_repo.get_by_id(letter.id)
        assert saved is not None

    def test_create_incoming(self, service: LetterService) -> None:
        letter = service.create_draft(
            letter_type=LetterType.INCOMING.value,
            subject="Incoming Request",
            body="Body",
            sender_id="ext-1",
            sender_name="External",
            sender_department="Other Org",
            department_id="dept-1",
            created_by_id="user-1",
        )
        assert letter.letter_type == LetterType.INCOMING.value

    def test_create_internal(self, service: LetterService) -> None:
        letter = service.create_draft(
            letter_type=LetterType.INTERNAL.value,
            subject="Internal Memo",
            body="Body",
            sender_id="user-1",
            sender_name="Ali",
            sender_department="HR",
            department_id="dept-1",
            created_by_id="user-1",
        )
        assert letter.letter_type == LetterType.INTERNAL.value

    def test_create_with_priority(self, service: LetterService) -> None:
        letter = service.create_draft(
            letter_type=LetterType.OUTGOING.value,
            subject="Urgent",
            body="Body",
            sender_id="u1",
            sender_name="U1",
            sender_department="D1",
            department_id="d1",
            created_by_id="u1",
            priority=LetterPriority.URGENT,
            classification=LetterClassification.CONFIDENTIAL,
        )
        assert letter.priority == LetterPriority.URGENT
        assert letter.classification == LetterClassification.CONFIDENTIAL


class TestEditDraft:
    def test_edit_subject(self, service: LetterService) -> None:
        letter = service.create_draft(
            letter_type=LetterType.OUTGOING.value,
            subject="Original",
            body="Body",
            sender_id="u1",
            sender_name="U1",
            sender_department="D1",
            department_id="d1",
            created_by_id="u1",
        )
        updated = service.edit_draft(letter.id, "u1", subject="Updated")
        assert updated.subject == "Updated"
        assert updated.version == 2

    def test_edit_not_found(self, service: LetterService) -> None:
        with pytest.raises(LetterNotFoundError):
            service.edit_draft("nonexistent", "u1", subject="Test")

    def test_edit_after_submit_raises(self, service: LetterService) -> None:
        letter = service.create_draft(
            letter_type=LetterType.OUTGOING.value,
            subject="No Edit",
            body="Body",
            sender_id="u1",
            sender_name="U1",
            sender_department="D1",
            department_id="d1",
            created_by_id="u1",
        )
        service.submit_for_review(letter.id, "u1")
        with pytest.raises(LetterNotEditableError):
            service.edit_draft(letter.id, "u1", subject="Trying")


class TestSubmitForReview:
    def test_submit(self, service: LetterService) -> None:
        letter = service.create_draft(
            letter_type=LetterType.OUTGOING.value,
            subject="Submit Test",
            body="Body",
            sender_id="u1",
            sender_name="U1",
            sender_department="D1",
            department_id="d1",
            created_by_id="u1",
        )
        updated = service.submit_for_review(letter.id, "u1")
        assert updated.status == LetterStatus.PENDING_REVIEW

    def test_submit_not_found(self, service: LetterService) -> None:
        with pytest.raises(LetterNotFoundError):
            service.submit_for_review("nonexistent", "u1")

    def test_submit_already_submitted_fails(self, service: LetterService) -> None:
        letter = service.create_draft(
            letter_type=LetterType.OUTGOING.value,
            subject="Double Submit",
            body="Body",
            sender_id="u1",
            sender_name="U1",
            sender_department="D1",
            department_id="d1",
            created_by_id="u1",
        )
        service.submit_for_review(letter.id, "u1")
        with pytest.raises(LetterServiceError):
            service.submit_for_review(letter.id, "u1")


class TestCancelLetter:
    def test_cancel_draft(self, service: LetterService) -> None:
        letter = service.create_draft(
            letter_type=LetterType.OUTGOING.value,
            subject="Cancel Test",
            body="Body",
            sender_id="u1",
            sender_name="U1",
            sender_department="D1",
            department_id="d1",
            created_by_id="u1",
        )
        updated = service.cancel_letter(letter.id, "u1", "No longer needed")
        assert updated.status == LetterStatus.DELETED

    def test_cancel_not_found(self, service: LetterService) -> None:
        with pytest.raises(LetterNotFoundError):
            service.cancel_letter("nonexistent", "u1")


class TestGetAndList:
    def test_get_letter_found(self, service: LetterService) -> None:
        letter = service.create_draft(
            letter_type=LetterType.OUTGOING.value,
            subject="Get Test",
            body="Body",
            sender_id="u1",
            sender_name="U1",
            sender_department="D1",
            department_id="d1",
            created_by_id="u1",
        )
        found = service.get_letter(letter.id)
        assert found is not None
        assert found.id == letter.id

    def test_get_letter_not_found(self, service: LetterService) -> None:
        assert service.get_letter("nonexistent") is None

    def test_list_by_status(self, service: LetterService) -> None:
        service.create_draft(
            letter_type=LetterType.OUTGOING.value,
            subject="A", body="B",
            sender_id="u1", sender_name="U1", sender_department="D1",
            department_id="d1", created_by_id="u1",
        )
        drafts = service.list_by_status(LetterStatus.DRAFT)
        assert len(drafts) == 1

    def test_list_by_department(self, service: LetterService) -> None:
        service.create_draft(
            letter_type=LetterType.OUTGOING.value,
            subject="A", body="B",
            sender_id="u1", sender_name="U1", sender_department="D1",
            department_id="dept-x", created_by_id="u1",
        )
        items = service.list_by_department("dept-x")
        assert len(items) == 1

    def test_count_by_status(self, service: LetterService) -> None:
        service.create_draft(
            letter_type=LetterType.OUTGOING.value,
            subject="A", body="B",
            sender_id="u1", sender_name="U1", sender_department="D1",
            department_id="d1", created_by_id="u1",
        )
        assert service.count_by_status(LetterStatus.DRAFT) == 1
        assert service.count_by_status(LetterStatus.APPROVED) == 0

    def test_count_by_department(self, service: LetterService) -> None:
        service.create_draft(
            letter_type=LetterType.OUTGOING.value,
            subject="A", body="B",
            sender_id="u1", sender_name="U1", sender_department="D1",
            department_id="dept-y", created_by_id="u1",
        )
        assert service.count_by_department("dept-y") == 1
        assert service.count_by_department("other") == 0
