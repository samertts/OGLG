from __future__ import annotations

import pytest

from app.application.letters.routing_service import RoutingService
from app.application.letters.letter_service import LetterService
from app.domain.letters.letter import LetterType
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
def service(letter_repo: InMemoryLetterRepo, audit_repo: InMemoryAuditRepo) -> RoutingService:
    return RoutingService(letter_repo, audit_repo, lambda: InMemoryUoW())


def make_letter(letter_repo: InMemoryLetterRepo) -> str:
    ls = LetterService(letter_repo, InMemoryAuditRepo(), lambda: InMemoryUoW())
    letter = ls.create_draft(
        letter_type=LetterType.OUTGOING.value,
        subject="Routing Test",
        body="Body",
        sender_id="user-1",
        sender_name="User",
        sender_department="DeptA",
        department_id="dept-a",
        created_by_id="user-1",
    )
    return letter.id


class TestRouteForward:
    def test_route_forward(self, service: RoutingService, letter_repo: InMemoryLetterRepo) -> None:
        letter_id = make_letter(letter_repo)
        updated = service.route_forward(
            letter_id=letter_id,
            from_user="user-1",
            from_department="DeptA",
            to_user="user-2",
            to_department="DeptB",
            user_id="user-1",
            notes="Please process",
        )
        assert len(updated.routing_history) == 1
        step = updated.routing_history[0]
        assert step.from_department == "DeptA"
        assert step.to_department == "DeptB"
        assert step.notes == "Please process"

    def test_route_forward_not_found(self, service: RoutingService) -> None:
        from app.application.letters.letter_service import LetterNotFoundError
        with pytest.raises(LetterNotFoundError):
            service.route_forward(
                letter_id="nonexistent",
                from_user="u1",
                from_department="D1",
                to_user="u2",
                to_department="D2",
                user_id="u1",
            )


class TestAcceptRouting:
    def test_accept_routing(self, service: RoutingService, letter_repo: InMemoryLetterRepo) -> None:
        letter_id = make_letter(letter_repo)
        updated = service.accept_routing(letter_id, "user-2", "DeptB")
        assert len(updated.routing_history) >= 1
        assert updated.routing_history[-1].action == "ACCEPT"

    def test_accept_routing_not_found(self, service: RoutingService) -> None:
        from app.application.letters.letter_service import LetterNotFoundError
        with pytest.raises(LetterNotFoundError):
            service.accept_routing("nonexistent", "u2", "DeptB")


class TestRejectRouting:
    def test_reject_routing(self, service: RoutingService, letter_repo: InMemoryLetterRepo) -> None:
        letter_id = make_letter(letter_repo)
        updated = service.reject_routing(letter_id, "user-2", "DeptB", "Wrong department")
        assert len(updated.routing_history) >= 1
        assert updated.routing_history[-1].action == "REJECT"

    def test_reject_routing_not_found(self, service: RoutingService) -> None:
        from app.application.letters.letter_service import LetterNotFoundError
        with pytest.raises(LetterNotFoundError):
            service.reject_routing("nonexistent", "u2", "DeptB", "reason")


class TestGetRoutingHistory:
    def test_get_history_empty(self, service: RoutingService, letter_repo: InMemoryLetterRepo) -> None:
        letter_id = make_letter(letter_repo)
        history = service.get_routing_history(letter_id)
        assert history == []

    def test_get_history_with_steps(self, service: RoutingService, letter_repo: InMemoryLetterRepo) -> None:
        letter_id = make_letter(letter_repo)
        service.route_forward(
            letter_id=letter_id,
            from_user="u1", from_department="D1",
            to_user="u2", to_department="D2",
            user_id="u1",
        )
        history = service.get_routing_history(letter_id)
        assert len(history) == 1

    def test_get_history_not_found(self, service: RoutingService) -> None:
        from app.application.letters.letter_service import LetterNotFoundError
        with pytest.raises(LetterNotFoundError):
            service.get_routing_history("nonexistent")
