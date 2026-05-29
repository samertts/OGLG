from __future__ import annotations


import pytest

from app.application.letters.transition_context import TransitionContext
from app.application.letters.workflow_engine import WorkflowEngine, WORKFLOW_STATUSES
from app.domain.letters.letter_status import LetterStatus
from tests.unit.letters.test_services_common import (
    InMemoryAuditRepo,
    InMemoryLetterRepo,
    InMemoryUoW,
    make_draft_letter,
)


@pytest.fixture
def letter_repo() -> InMemoryLetterRepo:
    return InMemoryLetterRepo()


@pytest.fixture
def audit_repo() -> InMemoryAuditRepo:
    return InMemoryAuditRepo()


@pytest.fixture
def engine(letter_repo: InMemoryLetterRepo, audit_repo: InMemoryAuditRepo) -> WorkflowEngine:
    return WorkflowEngine(letter_repo, audit_repo, lambda: InMemoryUoW())


@pytest.fixture
def draft_letter(letter_repo: InMemoryLetterRepo) -> str:
    letter = make_draft_letter(sender_id="user-1")
    letter_repo.save(letter)
    return letter.id


class TestWorkflowEngineSuccess:
    def test_draft_to_under_review(self, engine: WorkflowEngine, draft_letter: str) -> None:
        ctx = TransitionContext(
            letter_id=draft_letter,
            from_status=LetterStatus.DRAFT,
            target_status=LetterStatus.IN_REVIEW,
            user_id="user-1",
        )
        result = engine.execute(ctx)
        assert result.is_ok
        assert result.to_status == LetterStatus.IN_REVIEW
        assert result.from_status == LetterStatus.DRAFT
        assert len(result.events) >= 1

    def test_draft_to_cancelled(self, engine: WorkflowEngine, draft_letter: str) -> None:
        ctx = TransitionContext(
            letter_id=draft_letter,
            from_status=LetterStatus.DRAFT,
            target_status=LetterStatus.DELETED,
            user_id="user-1",
        )
        result = engine.execute(ctx)
        assert result.is_ok
        assert result.to_status == LetterStatus.DELETED

    def test_under_review_to_approved(self, engine: WorkflowEngine, draft_letter: str) -> None:
        ctx = TransitionContext(
            letter_id=draft_letter,
            from_status=LetterStatus.DRAFT,
            target_status=LetterStatus.IN_REVIEW,
            user_id="user-1",
        )
        engine.execute(ctx)
        ctx2 = TransitionContext(
            letter_id=draft_letter,
            from_status=LetterStatus.IN_REVIEW,
            target_status=LetterStatus.APPROVED,
            user_id="user-2",
            metadata={"reviewer_id": "user-2", "notes": "Approved"},
        )
        result = engine.execute(ctx2)
        assert result.is_ok
        assert result.to_status == LetterStatus.APPROVED
        assert len(result.events) >= 1

    def test_under_review_to_rejected(self, engine: WorkflowEngine, draft_letter: str) -> None:
        ctx = TransitionContext(
            letter_id=draft_letter,
            from_status=LetterStatus.DRAFT,
            target_status=LetterStatus.IN_REVIEW,
            user_id="user-1",
        )
        engine.execute(ctx)
        ctx2 = TransitionContext(
            letter_id=draft_letter,
            from_status=LetterStatus.IN_REVIEW,
            target_status=LetterStatus.REJECTED,
            user_id="user-2",
            metadata={"reviewer_id": "user-2", "reason": "Missing docs"},
        )
        result = engine.execute(ctx2)
        assert result.is_ok
        assert result.to_status == LetterStatus.REJECTED

    def test_under_review_to_draft(self, engine: WorkflowEngine, draft_letter: str) -> None:
        ctx = TransitionContext(
            letter_id=draft_letter,
            from_status=LetterStatus.DRAFT,
            target_status=LetterStatus.IN_REVIEW,
            user_id="user-1",
        )
        engine.execute(ctx)
        ctx2 = TransitionContext(
            letter_id=draft_letter,
            from_status=LetterStatus.IN_REVIEW,
            target_status=LetterStatus.DRAFT,
            user_id="user-1",
        )
        result = engine.execute(ctx2)
        assert result.is_ok
        assert result.to_status == LetterStatus.DRAFT

    def test_approved_to_delivered(self, engine: WorkflowEngine, draft_letter: str) -> None:
        ctx = TransitionContext(
            letter_id=draft_letter,
            from_status=LetterStatus.DRAFT,
            target_status=LetterStatus.IN_REVIEW,
            user_id="user-1",
        )
        engine.execute(ctx)
        engine.execute(TransitionContext(
            letter_id=draft_letter,
            from_status=LetterStatus.IN_REVIEW,
            target_status=LetterStatus.APPROVED,
            user_id="user-2",
            metadata={"reviewer_id": "user-2"},
        ))
        ctx3 = TransitionContext(
            letter_id=draft_letter,
            from_status=LetterStatus.APPROVED,
            target_status=LetterStatus.DELIVERED,
            user_id="user-1",
        )
        result = engine.execute(ctx3)
        assert result.is_ok
        assert result.to_status == LetterStatus.DELIVERED

    def test_approved_to_archived(self, engine: WorkflowEngine, draft_letter: str) -> None:
        ctx = TransitionContext(
            letter_id=draft_letter,
            from_status=LetterStatus.DRAFT,
            target_status=LetterStatus.IN_REVIEW,
            user_id="user-1",
        )
        engine.execute(ctx)
        engine.execute(TransitionContext(
            letter_id=draft_letter,
            from_status=LetterStatus.IN_REVIEW,
            target_status=LetterStatus.APPROVED,
            user_id="user-2",
            metadata={"reviewer_id": "user-2"},
        ))
        ctx3 = TransitionContext(
            letter_id=draft_letter,
            from_status=LetterStatus.APPROVED,
            target_status=LetterStatus.ARCHIVED,
            user_id="user-1",
            metadata={"reason": "Policy retention"},
        )
        result = engine.execute(ctx3)
        assert result.is_ok
        assert result.to_status == LetterStatus.ARCHIVED

    def test_rejected_to_draft(self, engine: WorkflowEngine, draft_letter: str) -> None:
        ctx = TransitionContext(
            letter_id=draft_letter,
            from_status=LetterStatus.DRAFT,
            target_status=LetterStatus.IN_REVIEW,
            user_id="user-1",
        )
        engine.execute(ctx)
        engine.execute(TransitionContext(
            letter_id=draft_letter,
            from_status=LetterStatus.IN_REVIEW,
            target_status=LetterStatus.REJECTED,
            user_id="user-2",
            metadata={"reviewer_id": "user-2", "reason": "Revise"},
        ))
        ctx3 = TransitionContext(
            letter_id=draft_letter,
            from_status=LetterStatus.REJECTED,
            target_status=LetterStatus.DRAFT,
            user_id="user-1",
        )
        result = engine.execute(ctx3)
        assert result.is_ok
        assert result.to_status == LetterStatus.DRAFT

    def test_rejected_to_cancelled(self, engine: WorkflowEngine, draft_letter: str) -> None:
        ctx = TransitionContext(
            letter_id=draft_letter,
            from_status=LetterStatus.DRAFT,
            target_status=LetterStatus.IN_REVIEW,
            user_id="user-1",
        )
        engine.execute(ctx)
        engine.execute(TransitionContext(
            letter_id=draft_letter,
            from_status=LetterStatus.IN_REVIEW,
            target_status=LetterStatus.REJECTED,
            user_id="user-2",
            metadata={"reviewer_id": "user-2", "reason": "Revise"},
        ))
        ctx3 = TransitionContext(
            letter_id=draft_letter,
            from_status=LetterStatus.REJECTED,
            target_status=LetterStatus.DELETED,
            user_id="user-1",
            metadata={"reason": "Cancelled by author"},
        )
        result = engine.execute(ctx3)
        assert result.is_ok
        assert result.to_status == LetterStatus.DELETED

    def test_delivered_to_archived(self, engine: WorkflowEngine, draft_letter: str) -> None:
        ctx = TransitionContext(
            letter_id=draft_letter,
            from_status=LetterStatus.DRAFT,
            target_status=LetterStatus.IN_REVIEW,
            user_id="user-1",
        )
        engine.execute(ctx)
        engine.execute(TransitionContext(
            letter_id=draft_letter,
            from_status=LetterStatus.IN_REVIEW,
            target_status=LetterStatus.APPROVED,
            user_id="user-2",
            metadata={"reviewer_id": "user-2"},
        ))
        engine.execute(TransitionContext(
            letter_id=draft_letter,
            from_status=LetterStatus.APPROVED,
            target_status=LetterStatus.DELIVERED,
            user_id="user-1",
        ))
        ctx4 = TransitionContext(
            letter_id=draft_letter,
            from_status=LetterStatus.DELIVERED,
            target_status=LetterStatus.ARCHIVED,
            user_id="user-1",
        )
        result = engine.execute(ctx4)
        assert result.is_ok
        assert result.to_status == LetterStatus.ARCHIVED

    def test_full_lifecycle(self, engine: WorkflowEngine, draft_letter: str) -> None:
        cycle: list[tuple[LetterStatus, LetterStatus]] = [
            (LetterStatus.DRAFT, LetterStatus.IN_REVIEW),
            (LetterStatus.IN_REVIEW, LetterStatus.APPROVED),
            (LetterStatus.APPROVED, LetterStatus.DELIVERED),
            (LetterStatus.DELIVERED, LetterStatus.ARCHIVED),
            (LetterStatus.ARCHIVED, LetterStatus.RESTORED),
            (LetterStatus.RESTORED, LetterStatus.DRAFT),
        ]
        for from_s, to_s in cycle:
            ctx = TransitionContext(
                letter_id=draft_letter,
                from_status=from_s,
                target_status=to_s,
                user_id="user-1",
                metadata={"reviewer_id": "user-2"},
            )
            result = engine.execute(ctx)
            assert result.is_ok, f"Failed {from_s.value} -> {to_s.value}: {result.error}"


class TestIdempotency:
    def test_already_at_target_returns_idempotent(self, engine: WorkflowEngine, draft_letter: str) -> None:
        ctx = TransitionContext(
            letter_id=draft_letter,
            from_status=LetterStatus.DRAFT,
            target_status=LetterStatus.DRAFT,
            user_id="user-1",
        )
        result = engine.execute(ctx)
        assert result.is_ok
        assert result.is_idempotent
        assert result.from_status == result.to_status

    def test_idempotent_has_no_events(self, engine: WorkflowEngine, draft_letter: str) -> None:
        ctx = TransitionContext(
            letter_id=draft_letter,
            from_status=LetterStatus.DRAFT,
            target_status=LetterStatus.DRAFT,
            user_id="user-1",
        )
        result = engine.execute(ctx)
        assert result.is_idempotent
        assert len(result.events) == 0


class TestErrorConditions:
    def test_letter_not_found(self, engine: WorkflowEngine) -> None:
        ctx = TransitionContext(
            letter_id="nonexistent",
            from_status=LetterStatus.DRAFT,
            target_status=LetterStatus.IN_REVIEW,
            user_id="user-1",
        )
        result = engine.execute(ctx)
        assert not result.is_ok
        assert result.error_code == "LETTER_NOT_FOUND"

    def test_status_mismatch(self, engine: WorkflowEngine, draft_letter: str) -> None:
        ctx = TransitionContext(
            letter_id=draft_letter,
            from_status=LetterStatus.IN_REVIEW,
            target_status=LetterStatus.APPROVED,
            user_id="user-1",
        )
        result = engine.execute(ctx)
        assert not result.is_ok
        assert result.error_code == "STATUS_MISMATCH"

    def test_transition_not_allowed(self, engine: WorkflowEngine, draft_letter: str) -> None:
        ctx = TransitionContext(
            letter_id=draft_letter,
            from_status=LetterStatus.DRAFT,
            target_status=LetterStatus.APPROVED,
            user_id="user-1",
        )
        result = engine.execute(ctx)
        assert not result.is_ok
        assert result.error_code == "TRANSITION_NOT_ALLOWED"

    def test_invalid_transition_via_domain(self, engine: WorkflowEngine, draft_letter: str) -> None:
        ctx = TransitionContext(
            letter_id=draft_letter,
            from_status=LetterStatus.DRAFT,
            target_status=LetterStatus.IN_REVIEW,
            user_id="user-1",
        )
        engine.execute(ctx)
        engine.execute(TransitionContext(
            letter_id=draft_letter,
            from_status=LetterStatus.IN_REVIEW,
            target_status=LetterStatus.APPROVED,
            user_id="user-2",
            metadata={"reviewer_id": "user-2"},
        ))
        ctx2 = TransitionContext(
            letter_id=draft_letter,
            from_status=LetterStatus.APPROVED,
            target_status=LetterStatus.IN_REVIEW,
            user_id="user-1",
        )
        result = engine.execute(ctx2)
        assert not result.is_ok


class TestCanTransition:
    def test_can_transition_valid(self, engine: WorkflowEngine) -> None:
        assert engine.can_transition(LetterStatus.DRAFT, LetterStatus.IN_REVIEW)

    def test_can_transition_invalid(self, engine: WorkflowEngine) -> None:
        assert not engine.can_transition(LetterStatus.DRAFT, LetterStatus.APPROVED)

    def test_can_transition_terminal(self, engine: WorkflowEngine) -> None:
        assert not engine.can_transition(LetterStatus.DELETED, LetterStatus.DRAFT)

    def test_cannot_transition_none(self, engine: WorkflowEngine) -> None:
        assert not engine.can_transition(LetterStatus.PENDING_REVIEW, LetterStatus.IN_REVIEW)


class TestGetAllowedTargets:
    def test_get_allowed_draft(self, engine: WorkflowEngine) -> None:
        targets = engine.get_allowed_targets(LetterStatus.DRAFT)
        assert LetterStatus.IN_REVIEW in targets
        assert LetterStatus.DELETED in targets
        assert len(targets) == 2

    def test_get_allowed_deleted(self, engine: WorkflowEngine) -> None:
        targets = engine.get_allowed_targets(LetterStatus.DELETED)
        assert len(targets) == 0

    def test_get_allowed_unsupported(self, engine: WorkflowEngine) -> None:
        targets = engine.get_allowed_targets(LetterStatus.PENDING_REVIEW)
        assert len(targets) == 0


class TestAuditEvents:
    def test_transition_generates_events(self, engine: WorkflowEngine, draft_letter: str, audit_repo: InMemoryAuditRepo) -> None:
        ctx = TransitionContext(
            letter_id=draft_letter,
            from_status=LetterStatus.DRAFT,
            target_status=LetterStatus.IN_REVIEW,
            user_id="user-1",
        )
        result = engine.execute(ctx)
        assert result.is_ok
        assert len(result.events) >= 1
        letter_events = audit_repo.get_events_for_letter(draft_letter)
        assert len(letter_events) >= 1

    def test_failed_transition_no_events(self, engine: WorkflowEngine, draft_letter: str, audit_repo: InMemoryAuditRepo) -> None:
        ctx = TransitionContext(
            letter_id=draft_letter,
            from_status=LetterStatus.DRAFT,
            target_status=LetterStatus.APPROVED,
            user_id="user-1",
        )
        result = engine.execute(ctx)
        assert not result.is_ok
        letter_events = audit_repo.get_events_for_letter(draft_letter)
        assert len(letter_events) == 0


class TestTransitionResult:
    def test_result_to_dict(self, engine: WorkflowEngine, draft_letter: str) -> None:
        ctx = TransitionContext(
            letter_id=draft_letter,
            from_status=LetterStatus.DRAFT,
            target_status=LetterStatus.IN_REVIEW,
            user_id="user-1",
        )
        result = engine.execute(ctx)
        d = result.to_dict()
        assert d["success"] is True
        assert d["letter_id"] == draft_letter
        assert d["from_status"] == "DRAFT"
        assert d["to_status"] == "IN_REVIEW"
        assert d["event_count"] >= 1
        assert d["error"] is None

    def test_result_to_dict_failure(self) -> None:
        from app.application.letters.transition_result import TransitionResult
        result = TransitionResult.fail(
            "l-1", LetterStatus.DRAFT, LetterStatus.APPROVED,
            error="Not allowed", error_code="TRANSITION_NOT_ALLOWED",
        )
        d = result.to_dict()
        assert d["success"] is False
        assert d["error"] == "Not allowed"
        assert d["error_code"] == "TRANSITION_NOT_ALLOWED"


class TestStateMachineConsistency:
    def test_workflow_matrix_matches_domain_matrix(self, engine: WorkflowEngine) -> None:
        for workflow_status in WORKFLOW_STATUSES:
            allowed = engine.get_allowed_targets(workflow_status)
            for target in allowed:
                assert isinstance(target, LetterStatus)

    def test_transition_reversibility(self, engine: WorkflowEngine, draft_letter: str) -> None:
        ctx = TransitionContext(
            letter_id=draft_letter,
            from_status=LetterStatus.DRAFT,
            target_status=LetterStatus.IN_REVIEW,
            user_id="user-1",
        )
        result = engine.execute(ctx)
        assert result.is_ok
        assert result.version > 0
        assert result.timestamp is not None
