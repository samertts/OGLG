from __future__ import annotations

import pytest

from app.application.letters.routing_context import RoutingContext
from app.application.letters.routing_result import RoutingResult
from app.application.letters.routing_service import RoutingService
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


def make_letter(letter_repo: InMemoryLetterRepo, audit_repo: InMemoryAuditRepo | None = None) -> str:
    from app.application.letters.letter_service import LetterService
    ar = audit_repo or InMemoryAuditRepo()
    ls = LetterService(letter_repo, ar, lambda: InMemoryUoW())
    letter = ls.create_draft(
        letter_type=LetterType.OUTGOING.value,
        subject="Routing Test", body="Body",
        sender_id="user-1", sender_name="User", sender_department="DeptA",
        department_id="dept-a", created_by_id="user-1",
    )
    letter.pop_events()
    return letter.id


def make_route_ctx(
    letter_id: str,
    from_dept: str = "DeptA",
    to_dept: str = "DeptB",
    from_user: str = "user-1",
    to_user: str = "user-2",
    user_id: str = "user-1",
    notes: str = "",
) -> RoutingContext:
    return RoutingContext(
        letter_id=letter_id,
        from_department=from_dept,
        from_user=from_user,
        to_department=to_dept,
        to_user=to_user,
        user_id=user_id,
        notes=notes,
    )


class TestRouteForward:
    def test_route_forward_success(self, service: RoutingService, letter_repo: InMemoryLetterRepo, audit_repo: InMemoryAuditRepo) -> None:
        letter_id = make_letter(letter_repo, audit_repo)
        ctx = make_route_ctx(letter_id)
        result = service.route_forward(ctx)
        assert result.is_ok
        assert result.action == "ROUTE"
        assert result.from_department == "DeptA"
        assert result.to_department == "DeptB"
        letter = letter_repo.get_by_id(letter_id)
        assert letter is not None
        assert len(letter.routing_history) == 1
        assert letter.routing_history[0].action == "ROUTE"

    def test_route_forward_not_found(self, service: RoutingService) -> None:
        from app.application.letters.letter_service import LetterNotFoundError
        ctx = make_route_ctx("nonexistent")
        with pytest.raises(LetterNotFoundError):
            service.route_forward(ctx)

    def test_route_forward_multiple_hops(self, service: RoutingService, letter_repo: InMemoryLetterRepo, audit_repo: InMemoryAuditRepo) -> None:
        letter_id = make_letter(letter_repo, audit_repo)
        r1 = service.route_forward(make_route_ctx(letter_id, from_dept="DeptA", to_dept="DeptB"))
        assert r1.is_ok
        r2 = service.route_forward(make_route_ctx(letter_id, from_dept="DeptB", to_dept="DeptC", user_id="user-2"))
        assert r2.is_ok
        letter = letter_repo.get_by_id(letter_id)
        assert letter is not None
        assert len(letter.routing_history) == 2

    def test_route_forward_generates_events(self, service: RoutingService, letter_repo: InMemoryLetterRepo, audit_repo: InMemoryAuditRepo) -> None:
        letter_id = make_letter(letter_repo, audit_repo)
        ctx = make_route_ctx(letter_id)
        result = service.route_forward(ctx)
        assert result.is_ok
        assert len(result.events) >= 1

    def test_route_forward_result_serialization(self, service: RoutingService, letter_repo: InMemoryLetterRepo, audit_repo: InMemoryAuditRepo) -> None:
        letter_id = make_letter(letter_repo, audit_repo)
        ctx = make_route_ctx(letter_id)
        result = service.route_forward(ctx)
        d = result.to_dict()
        assert d["success"] is True
        assert d["action"] == "ROUTE"
        assert d["from_department"] == "DeptA"
        assert d["to_department"] == "DeptB"
        assert d["event_count"] >= 1


class TestSelfRoutePrevention:
    def test_self_route_blocked(self, service: RoutingService, letter_repo: InMemoryLetterRepo, audit_repo: InMemoryAuditRepo) -> None:
        letter_id = make_letter(letter_repo, audit_repo)
        ctx = make_route_ctx(letter_id, from_dept="DeptA", to_dept="DeptA", from_user="u1", to_user="u1")
        result = service.route_forward(ctx)
        assert result.is_error
        assert result.error_code == "SELF_ROUTE"

    def test_self_route_same_department_different_user_allowed(self, service: RoutingService, letter_repo: InMemoryLetterRepo, audit_repo: InMemoryAuditRepo) -> None:
        letter_id = make_letter(letter_repo, audit_repo)
        ctx = make_route_ctx(letter_id, from_dept="DeptA", to_dept="DeptA", from_user="u1", to_user="u2")
        result = service.route_forward(ctx)
        assert result.is_ok


class TestCircularRoutePrevention:
    def test_circular_route_detected(self, service: RoutingService, letter_repo: InMemoryLetterRepo, audit_repo: InMemoryAuditRepo) -> None:
        letter_id = make_letter(letter_repo, audit_repo)
        r1 = service.route_forward(make_route_ctx(letter_id, from_dept="DeptA", to_dept="DeptB"))
        assert r1.is_ok
        r2 = service.route_forward(make_route_ctx(letter_id, from_dept="DeptB", to_dept="DeptC", user_id="user-2"))
        assert r2.is_ok
        ctx = make_route_ctx(letter_id, from_dept="DeptC", to_dept="DeptA", user_id="user-3")
        result = service.route_forward(ctx)
        assert result.is_error
        assert result.error_code == "CIRCULAR_ROUTE"

    def test_circular_to_self_department(self, service: RoutingService, letter_repo: InMemoryLetterRepo, audit_repo: InMemoryAuditRepo) -> None:
        letter_id = make_letter(letter_repo, audit_repo)
        service.route_forward(make_route_ctx(letter_id, from_dept="DeptA", to_dept="DeptB"))
        ctx = make_route_ctx(letter_id, from_dept="DeptB", to_dept="DeptA", user_id="user-2")
        result = service.route_forward(ctx)
        assert result.is_error
        assert result.error_code == "CIRCULAR_ROUTE"


class TestAcceptRouting:
    def test_accept_routing_success(self, service: RoutingService, letter_repo: InMemoryLetterRepo, audit_repo: InMemoryAuditRepo) -> None:
        letter_id = make_letter(letter_repo, audit_repo)
        service.route_forward(make_route_ctx(letter_id))
        result = service.accept_routing(letter_id, "user-2", "DeptB")
        assert result.is_ok
        assert result.action == "ACCEPT"
        letter = letter_repo.get_by_id(letter_id)
        assert letter is not None
        assert letter.routing_history[-1].action == "ACCEPT"

    def test_accept_routing_not_found(self, service: RoutingService) -> None:
        from app.application.letters.letter_service import LetterNotFoundError
        with pytest.raises(LetterNotFoundError):
            service.accept_routing("nonexistent", "u2", "DeptB")

    def test_accept_routing_no_history(self, service: RoutingService, letter_repo: InMemoryLetterRepo, audit_repo: InMemoryAuditRepo) -> None:
        letter_id = make_letter(letter_repo, audit_repo)
        result = service.accept_routing(letter_id, "user-2", "DeptB")
        assert result.is_error
        assert result.error_code == "NO_ROUTING_HISTORY"


class TestRejectRouting:
    def test_reject_routing_success(self, service: RoutingService, letter_repo: InMemoryLetterRepo, audit_repo: InMemoryAuditRepo) -> None:
        letter_id = make_letter(letter_repo, audit_repo)
        service.route_forward(make_route_ctx(letter_id))
        result = service.reject_routing(letter_id, "user-2", "DeptB", "Wrong dept")
        assert result.is_ok
        assert result.action == "REJECT"
        letter = letter_repo.get_by_id(letter_id)
        assert letter is not None
        assert letter.routing_history[-1].action == "REJECT"

    def test_reject_routing_not_found(self, service: RoutingService) -> None:
        from app.application.letters.letter_service import LetterNotFoundError
        with pytest.raises(LetterNotFoundError):
            service.reject_routing("nonexistent", "u2", "DeptB", "reason")

    def test_reject_routing_no_history(self, service: RoutingService, letter_repo: InMemoryLetterRepo, audit_repo: InMemoryAuditRepo) -> None:
        letter_id = make_letter(letter_repo, audit_repo)
        result = service.reject_routing(letter_id, "user-2", "DeptB", "reason")
        assert result.is_error
        assert result.error_code == "NO_ROUTING_HISTORY"


class TestGetRoutingHistory:
    def test_get_history_empty(self, service: RoutingService, letter_repo: InMemoryLetterRepo, audit_repo: InMemoryAuditRepo) -> None:
        letter_id = make_letter(letter_repo, audit_repo)
        history = service.get_routing_history(letter_id)
        assert history == []

    def test_get_history_with_steps(self, service: RoutingService, letter_repo: InMemoryLetterRepo, audit_repo: InMemoryAuditRepo) -> None:
        letter_id = make_letter(letter_repo, audit_repo)
        service.route_forward(make_route_ctx(letter_id))
        history = service.get_routing_history(letter_id)
        assert len(history) == 1

    def test_get_history_not_found(self, service: RoutingService) -> None:
        from app.application.letters.letter_service import LetterNotFoundError
        with pytest.raises(LetterNotFoundError):
            service.get_routing_history("nonexistent")

    def test_routing_history_is_immutable_copy(self, service: RoutingService, letter_repo: InMemoryLetterRepo, audit_repo: InMemoryAuditRepo) -> None:
        letter_id = make_letter(letter_repo, audit_repo)
        service.route_forward(make_route_ctx(letter_id))
        history = service.get_routing_history(letter_id)
        letter = letter_repo.get_by_id(letter_id)
        assert letter is not None
        assert history == letter.routing_history


class TestRoutingContext:
    def test_valid_routing_context(self) -> None:
        ctx = make_route_ctx("l-1")
        errors = ctx.validate()
        assert errors == []

    def test_invalid_routing_context(self) -> None:
        ctx = RoutingContext(letter_id="", from_department="", from_user="", to_department="", to_user="", user_id="")
        errors = ctx.validate()
        assert len(errors) == 6

    def test_self_route_property(self) -> None:
        ctx = make_route_ctx("l-1", from_dept="A", to_dept="A", from_user="u", to_user="u")
        assert ctx.is_self_route

    def test_non_self_route_property(self) -> None:
        ctx = make_route_ctx("l-1", from_dept="A", to_dept="B", from_user="u1", to_user="u2")
        assert not ctx.is_self_route

    def test_same_department_property(self) -> None:
        ctx = make_route_ctx("l-1", from_dept="A", to_dept="A")
        assert ctx.is_same_department

    def test_different_department_property(self) -> None:
        ctx = make_route_ctx("l-1", from_dept="A", to_dept="B")
        assert not ctx.is_same_department


class TestRoutingResult:
    def test_ok_constructor(self) -> None:
        result = RoutingResult.ok("l-1", "ROUTE", "A", "B")
        assert result.is_ok

    def test_fail_constructor(self) -> None:
        result = RoutingResult.fail("l-1", "ROUTE", "Blocked", "CIRCULAR_ROUTE", "A", "B")
        assert result.is_error
        assert result.error_code == "CIRCULAR_ROUTE"

    def test_to_dict(self) -> None:
        result = RoutingResult.ok("l-1", "ROUTE", "A", "B", routing_step_index=2)
        d = result.to_dict()
        assert d["action"] == "ROUTE"
        assert d["routing_step_index"] == 2
