from __future__ import annotations

from app.core.audit.chain import AuditChain
from app.core.audit.validator import AuditConsistencyValidator


def test_audit_chain_append() -> None:
    chain = AuditChain()
    entry = chain.append("letter.created", aggregate_id="letter-1", data={"ref": "L001"})
    assert entry.sequence == 1
    assert entry.event_type == "letter.created"
    assert entry.aggregate_id == "letter-1"
    assert entry.hash is not None
    assert chain.entry_count == 1


def test_audit_chain_chained_hashes() -> None:
    chain = AuditChain()
    e1 = chain.append("event.1", "agg-1", {"a": 1})
    e2 = chain.append("event.2", "agg-1", {"a": 2})
    assert e2.previous_hash == e1.hash
    assert chain.verify_chain()


def test_audit_chain_tamper_detection() -> None:
    chain = AuditChain()
    chain.append("event.1", "agg-1", {"a": 1})
    chain.append("event.2", "agg-1", {"a": 2})
    assert chain.verify_chain()
    entry = chain.get_entry(1)
    assert entry is not None
    assert chain.verify_chain()


def test_audit_chain_snapshot() -> None:
    chain = AuditChain()
    chain.append("event.1", "agg-1", {})
    chain.append("event.2", "agg-1", {})
    snap = chain.snapshot()
    assert snap.entry_count == 2
    assert snap.root_hash is not None
    assert snap.tip_hash is not None
    assert snap.root_hash != snap.tip_hash


def test_audit_validator_empty() -> None:
    chain = AuditChain()
    result = AuditConsistencyValidator.validate(chain)
    assert result["valid"]
    assert result["entry_count"] == 0


def test_audit_validator_consistent() -> None:
    chain = AuditChain()
    chain.append("event.1", "agg-1", {})
    result = AuditConsistencyValidator.validate(chain)
    assert result["valid"]


def test_audit_get_entries_since() -> None:
    chain = AuditChain()
    chain.append("event.1", "agg-1", {})
    chain.append("event.2", "agg-1", {})
    chain.append("event.3", "agg-1", {})
    since = chain.get_entries_since(1)
    assert len(since) == 2
    assert since[0].sequence == 2
