from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable


class WorkflowState(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    ROLLED_BACK = "rolled_back"


@dataclass
class AsyncWorkflow:
    workflow_id: str
    name: str
    state: WorkflowState = WorkflowState.PENDING
    progress: float = 0.0
    error_message: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    rollback_handler: Callable[[], None] | None = None

    def is_terminal(self) -> bool:
        return self.state in (
            WorkflowState.COMPLETED,
            WorkflowState.FAILED,
            WorkflowState.CANCELLED,
            WorkflowState.ROLLED_BACK,
        )

    def can_transition_to(self, target: WorkflowState) -> bool:
        if self.is_terminal():
            return False
        if self.state == WorkflowState.PENDING:
            return target in (WorkflowState.RUNNING, WorkflowState.CANCELLED)
        if self.state == WorkflowState.RUNNING:
            return target in (
                WorkflowState.COMPLETED,
                WorkflowState.FAILED,
                WorkflowState.CANCELLED,
                WorkflowState.ROLLED_BACK,
            )
        return False


@dataclass
class WorkflowContext:
    workflow: AsyncWorkflow
    caller_id: str | None = None
    rbac_context: dict[str, Any] = field(default_factory=dict)
    audit_token: str | None = None
    replay_id: str | None = None
