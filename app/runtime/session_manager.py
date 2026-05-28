"""Application session management.

Manages session lifecycle including initialization, activity tracking,
and proper teardown.
"""

from __future__ import annotations

import enum
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta

try:
    from app.runtime.runtime_context import RuntimeContext
except ImportError:

    class RuntimeContext:
        """Placeholder runtime context for session management."""

        def __init__(self) -> None:
            self.session_id: str | None = None


from app.utils.logger import get_logger

logger = get_logger("app.runtime.session_manager")


class SessionState(enum.Enum):
    """Possible states of an application session."""

    INACTIVE = "inactive"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CLOSED = "closed"


@dataclass
class SessionInfo:
    """Information about the current application session."""

    session_id: str
    started_at: datetime
    state: SessionState
    user_activity_count: int = 0


class SessionManager:
    """Manages the lifecycle of an application session.

    Provides session initialisation, state transitions, activity
    tracking, and summary reporting on close.
    """

    def __init__(self, context: RuntimeContext) -> None:
        self._context = context
        self._session_id: str = ""
        self._started_at: datetime | None = None
        self._state: SessionState = SessionState.INACTIVE
        self._activity_count: int = 0

    def initialize(self) -> None:
        """Create a new session and transition to ACTIVE state."""
        self._session_id = uuid.uuid4().hex[:16]
        self._started_at = datetime.now()
        self._state = SessionState.ACTIVE
        self._activity_count = 0
        logger.info(
            "Session initialized",
            extra={
                "session_id": self._session_id,
                "started_at": self._started_at.isoformat(),
            },
        )

    def suspend(self) -> None:
        """Suspend the session, transitioning to SUSPENDED state."""
        if self._state != SessionState.ACTIVE:
            logger.warning(
                "Cannot suspend non-active session",
                extra={"current_state": self._state.value},
            )
            return
        self._state = SessionState.SUSPENDED
        logger.info("Session suspended", extra={"session_id": self._session_id})

    def resume(self) -> None:
        """Resume a suspended session back to ACTIVE state."""
        if self._state != SessionState.SUSPENDED:
            logger.warning(
                "Cannot resume non-suspended session",
                extra={"current_state": self._state.value},
            )
            return
        self._state = SessionState.ACTIVE
        logger.info("Session resumed", extra={"session_id": self._session_id})

    def close(self) -> None:
        """Close the session and log a summary of session activity."""
        if self._state == SessionState.CLOSED:
            logger.warning("Session already closed")
            return
        self._state = SessionState.CLOSED
        duration = self.session_duration()
        logger.info(
            "Session closed",
            extra={
                "session_id": self._session_id,
                "duration_seconds": round(duration.total_seconds(), 1),
                "activity_count": self._activity_count,
            },
        )

    def record_activity(self) -> None:
        """Increment the user activity counter."""
        if self._state != SessionState.ACTIVE:
            logger.warning(
                "Activity recorded on non-active session",
                extra={"state": self._state.value},
            )
        self._activity_count += 1

    def session_info(self) -> SessionInfo:
        """Return information about the current session.

        Returns:
            SessionInfo with current session metadata.
        """
        return SessionInfo(
            session_id=self._session_id,
            started_at=self._started_at or datetime.now(),
            state=self._state,
            user_activity_count=self._activity_count,
        )

    def session_duration(self) -> timedelta:
        """Return the duration since the session started.

        Returns:
            timedelta representing elapsed session time.
        """
        if self._started_at is None:
            return timedelta()
        return datetime.now() - self._started_at

    def is_active(self) -> bool:
        """Check whether the session is in ACTIVE state.

        Returns:
            True if the session is active.
        """
        return self._state == SessionState.ACTIVE
