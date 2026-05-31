from __future__ import annotations

from app.core.federation.conflict import (
    ConflictType,
    EntityVersion,
    MergePolicy,
    SyncConflict,
)


def test_conflict_type_enum() -> None:
    assert ConflictType.VERSION_DIVERGENCE.value == "version_divergence"
    assert ConflictType.CONCURRENT_UPDATE.value == "concurrent_update"


def test_entity_version() -> None:
    v = EntityVersion(aggregate_id="agg-1", version=3, node_id="node-a")
    assert v.aggregate_id == "agg-1"
    assert v.version == 3
    assert v.node_id == "node-a"


def test_sync_conflict_default_policy() -> None:
    local_v = EntityVersion(aggregate_id="agg-1", version=1, node_id="local")
    remote_v = EntityVersion(aggregate_id="agg-1", version=2, node_id="remote")
    conflict = SyncConflict(
        conflict_id="c-1",
        conflict_type=ConflictType.VERSION_DIVERGENCE,
        aggregate_id="agg-1",
        local_version=local_v,
        remote_version=remote_v,
    )
    assert conflict.policy == MergePolicy.LAST_WRITE_WINS
    assert not conflict.resolved
