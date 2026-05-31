from __future__ import annotations

from app.core.federation.identity import (
    FederationNode,
    NodeAddress,
    NodeRole,
)


def test_federation_node_defaults() -> None:
    node = FederationNode()
    assert node.node_id is not None
    assert node.role == NodeRole.STANDALONE
    assert node.version == "1.0.0"


def test_federation_node_identity() -> None:
    node = FederationNode(
        node_id="node-1",
        institution_id="inst-1",
        branch_id="branch-1",
        role=NodeRole.BRANCH,
        version="2.0.0",
    )
    identity = node.identity()
    assert identity["node_id"] == "node-1"
    assert identity["institution_id"] == "inst-1"
    assert identity["role"] == "branch"
    assert identity["version"] == "2.0.0"


def test_federation_node_is_federated() -> None:
    standalone = FederationNode()
    assert not standalone.is_federated()
    federated = FederationNode(
        node_id="n-1",
        institution_id="i-1",
    )
    assert federated.is_federated()


def test_node_address_local() -> None:
    addr = NodeAddress(hostname="", port=0)
    assert addr.is_local()
    remote = NodeAddress(hostname="192.168.1.100", port=8080)
    assert not remote.is_local()
