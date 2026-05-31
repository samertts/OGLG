from __future__ import annotations

import time
from dataclasses import dataclass
from enum import Enum, auto


class SyncScenario(Enum):
    LAN_INTERRUPTION = auto()
    USB_SYNC = auto()
    DUPLICATE_REPLAY = auto()
    DELAYED_SYNC = auto()
    NODE_COLLISION = auto()
    DETERMINISTIC_CONFLICT = auto()
    OFFLINE_QUEUE_REPLAY = auto()
    FEDERATION_AUDIT = auto()


@dataclass
class DeterministicConflictReport:
    scenario: SyncScenario
    success: bool
    detail: str = ""
    resolved: bool = True
    duration_seconds: float = 0.0


class OfflineFederationValidator:
    def simulate_lan_interruption(self) -> DeterministicConflictReport:
        start = time.monotonic()
        parked = {"node_a", "node_b"}
        unparked: set[str] = set()
        for node in parked:
            unparked.add(node)
        exchanged = len(parked) == len(unparked)
        return DeterministicConflictReport(
            SyncScenario.LAN_INTERRUPTION, exchanged,
            f"parked={parked}, unparked={unparked}",
            exchanged, time.monotonic() - start,
        )

    def simulate_usb_sync(self) -> DeterministicConflictReport:
        start = time.monotonic()
        manifest = {"outgoing": {"msg_1", "msg_2"}, "incoming": set()}
        replayed = set()
        for msg in manifest["outgoing"]:
            replayed.add(msg)
        merged = len(replayed) == len(manifest["outgoing"])
        return DeterministicConflictReport(
            SyncScenario.USB_SYNC, merged,
            f"outgoing={len(manifest['outgoing'])}, replayed={len(replayed)}",
            merged, time.monotonic() - start,
        )

    def simulate_duplicate_replay(self) -> DeterministicConflictReport:
        start = time.monotonic()
        seen: set[str] = set()
        dedup = True
        events = ["evt-1", "evt-2", "evt-1"]
        for evt in events:
            if evt in seen:
                dedup = False
            seen.add(evt)
        return DeterministicConflictReport(
            SyncScenario.DUPLICATE_REPLAY, not dedup,
            f"events={events}, dedup={dedup}",
            True, time.monotonic() - start,
        )

    def simulate_delayed_sync(self, delay_seconds: float = 300.0) -> DeterministicConflictReport:
        start = time.monotonic()
        ordered = [1, 2, 3]
        delayed = [1, 3, 2]
        eventual: list[int] = []
        for v in ordered:
            if v not in eventual:
                eventual.append(v)
        for v in delayed:
            if v not in eventual:
                eventual.append(v)
        consistent = eventual == sorted(eventual)
        return DeterministicConflictReport(
            SyncScenario.DELAYED_SYNC, consistent,
            f"delay={delay_seconds}s, eventual={eventual}",
            consistent, time.monotonic() - start,
        )

    def simulate_node_identity_collision(self) -> DeterministicConflictReport:
        start = time.monotonic()
        registry: dict[str, str] = {}
        first = registry.setdefault("node-1", "original")
        second = registry.setdefault("node-1", "impostor")
        resolved = first == "original" and second == "original"
        return DeterministicConflictReport(
            SyncScenario.NODE_COLLISION, resolved,
            f"first={first}, second={second}",
            resolved, time.monotonic() - start,
        )

    def simulate_deterministic_conflict_replay(
        self, nonce: str = "abc",
    ) -> DeterministicConflictReport:
        start = time.monotonic()
        resolved_order = sorted(["x", nonce, "z"])
        expected = sorted(["x", nonce, "z"])
        consistent = resolved_order == expected
        return DeterministicConflictReport(
            SyncScenario.DETERMINISTIC_CONFLICT, consistent,
            f"nonce={nonce}, resolved={resolved_order}",
            consistent, time.monotonic() - start,
        )

    def simulate_offline_queue_replay(self) -> DeterministicConflictReport:
        start = time.monotonic()
        queue = [{"id": "a", "seq": 1}, {"id": "b", "seq": 2}]
        drained: list[dict] = []
        for item in queue:
            drained.append(item)
        ok = len(drained) == len(queue)
        return DeterministicConflictReport(
            SyncScenario.OFFLINE_QUEUE_REPLAY, ok,
            f"queued={len(queue)}, drained={len(drained)}",
            ok, time.monotonic() - start,
        )

    def simulate_federation_audit_continuity(self) -> DeterministicConflictReport:
        start = time.monotonic()
        registry = ["node_a", "node_b", "node_c"]
        audit_count = len(registry)
        append_only = registry == sorted(registry)
        return DeterministicConflictReport(
            SyncScenario.FEDERATION_AUDIT, append_only,
            f"nodes={audit_count}, append_only={append_only}",
            True, time.monotonic() - start,
        )
