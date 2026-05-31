from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.core.events.bus import EventBus
from app.core.events.store import EventStore


class ReplayManager:
    """Bounded replay-safe event restoration with checkpoint tracking."""

    def __init__(
        self,
        store: EventStore,
        bus: EventBus,
        max_batch: int = 1000,
    ) -> None:
        self._store = store
        self._bus = bus
        self._max_batch = max_batch

    def replay_from_checkpoint(
        self,
        checkpoint_id: str = "default",
        force: bool = False,
    ) -> dict[str, Any]:
        from_seq = self._store.load_checkpoint(checkpoint_id)
        if from_seq == 0 and not force and self._store.max_sequence > 0:
            return {
                "replayed": 0,
                "from_sequence": 0,
                "message": "No checkpoint found — use force=True for initial replay",
            }
        total = 0
        last_seq = from_seq
        while True:
            events = self._store.read_since(
                sequence=last_seq,
                limit=self._max_batch,
            )
            if not events:
                break
            self._bus.replay(events)
            total += len(events)
            last_seq = events[-1].metadata.sequence
            if len(events) < self._max_batch:
                break
        self._store.save_checkpoint(checkpoint_id)
        return {
            "replayed": total,
            "from_sequence": from_seq,
            "to_sequence": last_seq,
            "checkpoint": checkpoint_id,
            "completed_at": datetime.now(timezone.utc).isoformat(),
        }

    def set_checkpoint(self, checkpoint_id: str = "default") -> str:
        return self._store.save_checkpoint(checkpoint_id)

    def get_checkpoint_sequence(
        self, checkpoint_id: str = "default"
    ) -> int:
        return self._store.load_checkpoint(checkpoint_id)

    def state(self) -> dict[str, Any]:
        return {
            "max_batch": self._max_batch,
            "max_store_sequence": self._store.max_sequence,
            "store_event_count": self._store.event_count,
        }
