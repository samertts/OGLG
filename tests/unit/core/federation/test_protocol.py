from __future__ import annotations

from app.core.federation.identity import FederationNode
from app.core.federation.protocol import FederationProtocol


def test_protocol_emit_event() -> None:
    local = FederationNode(node_id="node-local", label="HQ")
    proto = FederationProtocol(local_node=local)
    event = proto.emit(
        event_type="letter.created",
        aggregate_id="letter-1",
        data={"subject": "Test"},
    )
    assert event.event_type == "letter.created"
    assert event.aggregate_id == "letter-1"
    assert event.source == "node-local"
    assert proto.pending_count == 1


def test_protocol_register_peer() -> None:
    local = FederationNode(node_id="node-a", label="A")
    peer = FederationNode(node_id="node-b", label="B")
    proto = FederationProtocol(local_node=local)
    proto.register_peer(peer)
    assert proto.peer_count == 1
    assert proto.get_peer("node-b") is not None


def test_protocol_prepare_sync() -> None:
    local = FederationNode(node_id="node-a", label="A")
    peer = FederationNode(node_id="node-b", label="B")
    proto = FederationProtocol(local_node=local)
    proto.register_peer(peer)
    proto.emit("event.1", "agg-1", {"data": 1})
    manifest = proto.prepare_sync("node-b")
    assert manifest is not None
    assert len(manifest.events) == 1
    assert manifest.source_node == "node-a"
    assert manifest.target_node == "node-b"


def test_protocol_receive_sync() -> None:
    local_a = FederationNode(node_id="node-a", label="A")
    local_b = FederationNode(node_id="node-b", label="B")
    proto_a = FederationProtocol(local_node=local_a)
    proto_b = FederationProtocol(local_node=local_b)
    proto_b.register_peer(local_a)

    proto_a.register_peer(local_b)
    proto_a.emit("event.1", "agg-1", {"data": "hello"})
    manifest = proto_a.prepare_sync("node-b")
    assert manifest is not None

    session = proto_b.receive_sync(manifest)
    assert session.events_synced == 1
    assert proto_b.pending_count == 1


def test_protocol_prepare_sync_no_peer() -> None:
    local = FederationNode(node_id="node-a")
    proto = FederationProtocol(local_node=local)
    manifest = proto.prepare_sync("nonexistent")
    assert manifest is None


def test_protocol_state() -> None:
    local = FederationNode(node_id="node-a", label="A")
    peer = FederationNode(node_id="node-b", label="B")
    proto = FederationProtocol(local_node=local)
    proto.register_peer(peer)
    state = proto.state()
    assert state["local_node"] == "node-a"
    assert "node-b" in state["peers"]
