from __future__ import annotations

from typing import Any

from app.core.audit.chain import AuditChain


class AuditConsistencyValidator:
    """Validates audit chain consistency and tamper detection."""

    @staticmethod
    def validate(chain: AuditChain) -> dict[str, Any]:
        if chain.entry_count == 0:
            return {
                "valid": True,
                "message": "Empty chain is valid",
                "entry_count": 0,
            }
        chain_valid = chain.verify_chain()
        if not chain_valid:
            return {
                "valid": False,
                "message": "Chain integrity check failed — hash mismatch",
                "entry_count": chain.entry_count,
                "root_hash": chain.root_hash,
                "tip_hash": chain.tip_hash,
            }
        snapshot = chain.snapshot()
        return {
            "valid": True,
            "message": "Audit chain consistent",
            "entry_count": snapshot.entry_count,
            "root_hash": snapshot.root_hash,
            "tip_hash": snapshot.tip_hash,
            "sequence": snapshot.sequence,
        }

    @staticmethod
    def detect_tamper(chain: AuditChain) -> list[dict[str, Any]]:
        tampered: list[dict[str, Any]] = []
        entries = chain._entries  # type: ignore[arg-type]
        for i, entry in enumerate(entries):
            if entry.hash != entry.compute_hash():
                tampered.append(
                    {
                        "sequence": entry.sequence,
                        "entry_id": entry.entry_id,
                        "expected_hash": entry.compute_hash(),
                        "stored_hash": entry.hash,
                    }
                )
            if i > 0 and entry.previous_hash != entries[i - 1].hash:
                tampered.append(
                    {
                        "sequence": entry.sequence,
                        "entry_id": entry.entry_id,
                        "issue": "previous_hash mismatch",
                        "expected_previous": entries[i - 1].hash,
                        "stored_previous": entry.previous_hash,
                    }
                )
        return tampered
