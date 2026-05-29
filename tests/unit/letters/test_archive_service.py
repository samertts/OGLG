from __future__ import annotations

import pytest

from app.application.letters.archive_service import ArchiveService, ArchiveServiceError
from app.application.letters.letter_service import LetterService
from app.domain.letters.letter import LetterType
from app.domain.letters.letter_status import LetterStatus
from app.domain.letters.archive_state import ArchiveState
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
def service(letter_repo: InMemoryLetterRepo, audit_repo: InMemoryAuditRepo) -> ArchiveService:
    return ArchiveService(letter_repo, audit_repo, lambda: InMemoryUoW())


def make_approvable_letter(letter_repo: InMemoryLetterRepo) -> str:
    ls = LetterService(letter_repo, InMemoryAuditRepo(), lambda: InMemoryUoW())
    letter = ls.create_draft(
        letter_type=LetterType.OUTGOING.value,
        subject="Archive Test",
        body="Body",
        sender_id="user-1",
        sender_name="User",
        sender_department="Dept",
        department_id="dept-1",
        created_by_id="user-1",
    )
    ls.submit_for_review(letter.id, "user-1")
    approval = __import__("app.application.letters.approval_service", fromlist=["ApprovalService"])
    asvc = approval.ApprovalService(letter_repo, InMemoryAuditRepo(), lambda: InMemoryUoW())
    asvc.assign_reviewer(letter.id, "reviewer-1", "Reviewer 1", "Reviewer", "user-1")
    asvc.start_review(letter.id, "reviewer-1")
    asvc.approve(letter.id, "reviewer-1", "reviewer-1")
    return letter.id


class TestArchive:
    def test_archive_letter(self, service: ArchiveService, letter_repo: InMemoryLetterRepo) -> None:
        letter_id = make_approvable_letter(letter_repo)
        updated = service.archive(letter_id, "user-1", "Retention complete")
        assert updated.status == LetterStatus.ARCHIVED
        assert updated.archive_state == ArchiveState.ARCHIVED
        assert updated.is_archived

    def test_archive_not_found(self, service: ArchiveService) -> None:
        from app.application.letters.letter_service import LetterNotFoundError
        with pytest.raises(LetterNotFoundError):
            service.archive("nonexistent", "u1")

    def test_archive_draft_fails(self, service: ArchiveService, letter_repo: InMemoryLetterRepo) -> None:
        ls = LetterService(letter_repo, InMemoryAuditRepo(), lambda: InMemoryUoW())
        letter = ls.create_draft(
            letter_type=LetterType.OUTGOING.value,
            subject="Draft", body="Body",
            sender_id="u1", sender_name="U1", sender_department="D1",
            department_id="d1", created_by_id="u1",
        )
        with pytest.raises(ArchiveServiceError):
            service.archive(letter.id, "u1")


class TestRestore:
    def test_restore_letter(self, service: ArchiveService, letter_repo: InMemoryLetterRepo) -> None:
        letter_id = make_approvable_letter(letter_repo)
        service.archive(letter_id, "user-1", "Archive")
        updated = service.restore(letter_id, "user-1", "Need to amend")
        assert updated.status == LetterStatus.RESTORED
        assert updated.archive_state == ArchiveState.ACTIVE
        assert not updated.is_archived

    def test_restore_not_found(self, service: ArchiveService) -> None:
        from app.application.letters.letter_service import LetterNotFoundError
        with pytest.raises(LetterNotFoundError):
            service.restore("nonexistent", "u1")

    def test_restore_draft_fails(self, service: ArchiveService, letter_repo: InMemoryLetterRepo) -> None:
        ls = LetterService(letter_repo, InMemoryAuditRepo(), lambda: InMemoryUoW())
        letter = ls.create_draft(
            letter_type=LetterType.OUTGOING.value,
            subject="Draft", body="Body",
            sender_id="u1", sender_name="U1", sender_department="D1",
            department_id="d1", created_by_id="u1",
        )
        with pytest.raises(ArchiveServiceError):
            service.restore(letter.id, "u1")


class TestSoftDelete:
    def test_soft_delete(self, service: ArchiveService, letter_repo: InMemoryLetterRepo) -> None:
        ls = LetterService(letter_repo, InMemoryAuditRepo(), lambda: InMemoryUoW())
        letter = ls.create_draft(
            letter_type=LetterType.OUTGOING.value,
            subject="Delete Me", body="Body",
            sender_id="u1", sender_name="U1", sender_department="D1",
            department_id="d1", created_by_id="u1",
        )
        updated = service.soft_delete(letter.id, "u1", "Remove")
        assert updated.status == LetterStatus.DELETED
        assert updated.archive_state == ArchiveState.SOFT_DELETED

    def test_soft_delete_not_found(self, service: ArchiveService) -> None:
        from app.application.letters.letter_service import LetterNotFoundError
        with pytest.raises(LetterNotFoundError):
            service.soft_delete("nonexistent", "u1")


class TestListAndCount:
    def test_list_archived(self, service: ArchiveService, letter_repo: InMemoryLetterRepo) -> None:
        letter_id = make_approvable_letter(letter_repo)
        service.archive(letter_id, "u1")
        archived = service.list_archived()
        assert len(archived) >= 1

    def test_list_deleted(self, service: ArchiveService, letter_repo: InMemoryLetterRepo) -> None:
        ls = LetterService(letter_repo, InMemoryAuditRepo(), lambda: InMemoryUoW())
        letter = ls.create_draft(
            letter_type=LetterType.OUTGOING.value,
            subject="Del", body="B",
            sender_id="u1", sender_name="U1", sender_department="D1",
            department_id="d1", created_by_id="u1",
        )
        service.soft_delete(letter.id, "u1", "Remove")
        deleted = service.list_deleted()
        assert len(deleted) >= 1

    def test_count_archived(self, service: ArchiveService, letter_repo: InMemoryLetterRepo) -> None:
        letter_id = make_approvable_letter(letter_repo)
        service.archive(letter_id, "u1")
        assert service.count_archived() >= 1
        assert service.count_deleted() == 0
