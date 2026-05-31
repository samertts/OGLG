from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto


class ApprovalDecision(Enum):
    PENDING = auto()
    APPROVED = auto()
    REJECTED = auto()


@dataclass
class ApprovalStep:
    step_id: str
    role_name: str
    order: int = 0
    decision: ApprovalDecision = ApprovalDecision.PENDING
    decided_by: str | None = None
    decided_at: datetime | None = None
    comment: str = ""

    @property
    def is_decided(self) -> bool:
        return self.decision != ApprovalDecision.PENDING


@dataclass
class ApprovalRoute:
    route_id: str
    name: str = ""
    steps: list[ApprovalStep] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def add_step(self, role_name: str, order: int) -> ApprovalStep:
        step = ApprovalStep(
            step_id=f"step_{len(self.steps) + 1}",
            role_name=role_name,
            order=order,
        )
        self.steps.append(step)
        return step

    @property
    def pending_steps(self) -> list[ApprovalStep]:
        return [s for s in self.steps if s.decision == ApprovalDecision.PENDING]

    @property
    def all_approved(self) -> bool:
        return all(s.decision == ApprovalDecision.APPROVED for s in self.steps)

    @property
    def any_rejected(self) -> bool:
        return any(s.decision == ApprovalDecision.REJECTED for s in self.steps)


class ApprovalRouter:
    def __init__(self) -> None:
        self._routes: dict[str, ApprovalRoute] = {}

    @property
    def route_count(self) -> int:
        return len(self._routes)

    def create_route(self, route_id: str, name: str = "") -> ApprovalRoute:
        route = ApprovalRoute(route_id=route_id, name=name or route_id)
        self._routes[route_id] = route
        return route

    def get_route(self, route_id: str) -> ApprovalRoute | None:
        return self._routes.get(route_id)

    def decide_step(
        self, route_id: str, step_id: str,
        decision: ApprovalDecision, decided_by: str,
        comment: str = "",
    ) -> bool:
        route = self._routes.get(route_id)
        if route is None:
            return False
        for step in route.steps:
            if step.step_id == step_id and not step.is_decided:
                step.decision = decision
                step.decided_by = decided_by
                step.decided_at = datetime.now(timezone.utc)
                step.comment = comment
                return True
        return False

    def delete_route(self, route_id: str) -> bool:
        return self._routes.pop(route_id, None) is not None

    def clear(self) -> None:
        self._routes.clear()
