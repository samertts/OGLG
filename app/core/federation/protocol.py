from __future__ import annotations

import hashlib
import json
import threading
import uuid
from datetime import datetime, timezone
from typing import Any

from app.core.federation.contracts import (
    FederationEvent,
    SyncCheckpoint,
    SyncManifest,
    SyncMetadata,
    SyncSession,
)
from app.core.federation.identity import FederationNode, NodeId


class FederationProtocol:
    """Local federation protocol with bounded sync sessions."""

    def __init__(
        self,
        local_node: FederationNode,
        max_events_per_sync: int = 1000,
    ) -> None:
        self._local = local_node
        self._max_events = max_events_per_sync
        self._peers: dict[NodeId, FederationNode] = {}
        self._lock = threading.RLock()
        self._pending: list[FederationEvent] = []
        self._checkpoints: dict[NodeId, SyncCheckpoint] = {}
        self._sessions: list[SyncSession] = []

    @property
    def local_node(self) -> FederationNode:
        return self._local

    def register_peer(self, node: FederationNode) -> None:
        with self._lock:
            self._peers[node.node_id] = node

    def unregister_peer(self, node_id: NodeId) -> None:
        with self._lock:
            self._peers.pop(node_id, None)

    def get_peer(self, node_id: NodeId) -> FederationNode | None:
        return self._peers.get(node_id)

    @property
    def peer_count(self) -> int:
        return len(self._peers)

    def emit(
        self,
        event_type: str,
        aggregate_id: str,
        data: dict[str, Any],
        target_node: NodeId = "",
    ) -> FederationEvent:
        metadata = SyncMetadata(
            sync_id=uuid.uuid4().hex,
            source_node=self._local.node_id,
            target_node=target_node or self._local.node_id,
            timestamp=datetime.now(timezone.utc),
            sequence=len(self._pending) + 1,
            checksum=self._compute_checksum(event_type, aggregate_id, data),
        )
        event = FederationEvent(
            event_type=event_type,
            source=self._local.node_id,
            aggregate_id=aggregate_id,
            data=data,
            metadata=metadata,
        )
        with self._lock:
            self._pending.append(event)
        return event

    def prepare_sync(
        self,
        target_node: NodeId,
    ) -> SyncManifest | None:
        with self._lock:
            if target_node not in self._peers:
                return None
            checkpoint = self._checkpoints.get(target_node)
            from_seq = checkpoint.sequence if checkpoint else 0
            events = [
                e for e in self._pending
                if e.metadata.sequence > from_seq
            ][: self._max_events]
            if not events:
                return None
            manifest = SyncManifest(
                source_node=self._local.node_id,
                target_node=target_node,
                events=events,
                checkpoint=checkpoint.checksum if checkpoint else "",
                checksum=self._compute_manifest_checksum(events),
            )
            return manifest

    def receive_sync(
        self,
        manifest: SyncManifest,
    ) -> SyncSession:
        session = SyncSession(
            session_id=uuid.uuid4().hex,
            source_node=manifest.source_node,
            target_node=self._local.node_id,
        )
        session.start()
        for event in manifest.events:
            try:
                with self._lock:
                    self._pending.append(event)
                    session.events_synced += 1
            except Exception as exc:
                session.errors.append(str(exc))
        checkpoint = SyncCheckpoint(
            node_id=manifest.source_node,
            sequence=len(manifest.events),
            timestamp=datetime.now(timezone.utc),
            checksum=manifest.checksum,
        )
        with self._lock:
            self._checkpoints[manifest.source_node] = checkpoint
            self._sessions.append(session)
        session.complete()
        return session

    def get_checkpoint(self, node_id: NodeId) -> SyncCheckpoint | None:
        return self._checkpoints.get(node_id)

    @property
    def pending_count(self) -> int:
        return len(self._pending)

    def state(self) -> dict[str, Any]:
        with self._lock:
            return {
                "local_node": self._local.node_id,
                "peers": list(self._peers.keys()),
                "pending_events": len(self._pending),
                "sessions": len(self._sessions),
                "checkpoints": {
                    nid: {"sequence": cp.sequence, "checksum": cp.checksum}
                    for nid, cp in self._checkpoints.items()
                },
            }

    @staticmethod
    def _compute_checksum(
        event_type: str,
        aggregate_id: str,
        data: dict[str, Any],
    ) -> str:
        raw = f"{event_type}:{aggregate_id}:{json.dumps(data, sort_keys=True)}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    @staticmethod
    def _compute_manifest_checksum(
        events: list[FederationEvent],
    ) -> str:
        raw = "|".join(
            f"{e.event_type}:{e.aggregate_id}:{e.metadata.sequence}"
            for e in events
        )
        return hashlib.sha256(raw.encode()).hexdigest()[:16]
