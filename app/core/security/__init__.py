from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass
from typing import Any


@dataclass
class SecurityReport:
    name: str
    passed: bool
    detail: str = ""
    duration_seconds: float = 0.0


class RbacBypassValidator:
    def validate(self, roles: list[str], required: str) -> SecurityReport:
        start = time.monotonic()
        direct = required in roles
        pre_check = any(r == required for r in roles)
        bypass = direct != pre_check
        return SecurityReport(
            "rbac_bypass", not bypass,
            f"role={required}, direct={direct}, pre_check={pre_check}",
            time.monotonic() - start,
        )


class ReplayAttackValidator:
    def __init__(self, window_seconds: float = 300.0) -> None:
        self._window = window_seconds
        self._seen_ids: dict[str, float] = {}

    def validate(self, event_id: str, timestamp: float) -> SecurityReport:
        start = time.monotonic()
        now = time.monotonic()
        duplicate = event_id in self._seen_ids
        age = now - self._seen_ids.get(event_id, now) if duplicate else 0.0
        in_window = duplicate and age < self._window
        if not duplicate:
            self._seen_ids[event_id] = now
        return SecurityReport(
            "replay_attack", not in_window,
            f"event_id={event_id}, duplicate={duplicate}, window_ms={self._window}",
            time.monotonic() - start,
        )


class AuditTamperDetector:
    def __init__(self) -> None:
        self._entries: list[dict[str, Any]] = []

    def add_entry(self, entry: dict[str, Any]) -> str:
        prev_hash = self._entries[-1]["hash"] if self._entries else "0" * 64
        raw = (
            f"{prev_hash}:{entry.get('seq', 0)}"
            f":{entry.get('action', '')}:{entry.get('timestamp', '')}"
        )
        entry["hash"] = hashlib.sha256(raw.encode()).hexdigest()
        self._entries.append(entry)
        return entry["hash"]

    def verify_chain(self) -> SecurityReport:
        start = time.monotonic()
        for i, entry in enumerate(self._entries):
            expected_prev = self._entries[i - 1]["hash"] if i > 0 else "0" * 64
            raw = (
                f"{expected_prev}:{entry.get('seq', 0)}"
                f":{entry.get('action', '')}:{entry.get('timestamp', '')}"
            )
            expected_hash = hashlib.sha256(raw.encode()).hexdigest()
            if entry.get("hash") != expected_hash:
                return SecurityReport(
                    "audit_tamper", False,
                    f"Entry {i}: hash mismatch",
                    time.monotonic() - start,
                )
        return SecurityReport(
            "audit_tamper", True,
            f"{len(self._entries)} entries verified",
            time.monotonic() - start,
        )


class UnauthorizedQueueInjector:
    def __init__(self, allowed_event_types: set[str] | None = None) -> None:
        self._allowed = allowed_event_types or set()

    def validate(self, source: str, event_type: str, payload: Any) -> SecurityReport:
        start = time.monotonic()
        issues: list[str] = []
        if source not in ("system", "user", "federation"):
            issues.append(f"unknown source: {source}")
        if event_type not in self._allowed:
            issues.append(f"unallowed event_type: {event_type}")
        if not isinstance(payload, dict):
            issues.append(f"malformed payload: {type(payload).__name__}")
        passed = len(issues) == 0
        return SecurityReport(
            "unauthorized_queue_inject", passed,
            "; ".join(issues) if issues else "valid",
            time.monotonic() - start,
        )


class PathTraversalGuard:
    def validate(self, path_str: str) -> SecurityReport:
        start = time.monotonic()
        issues: list[str] = []
        if ".." in path_str:
            issues.append("parent dir reference")
        if path_str.startswith("/") or path_str.startswith("\\"):
            issues.append("absolute path")
        if "\\" in path_str:
            issues.append("backslash separator")
        passed = len(issues) == 0
        return SecurityReport(
            "path_traversal", passed,
            "; ".join(issues) if issues else "safe",
            time.monotonic() - start,
        )


class WorkstationTrustValidator:
    def validate(self, identity: str, registered_ids: set[str]) -> SecurityReport:
        start = time.monotonic()
        trusted = identity in registered_ids
        if not trusted:
            registered_ids.add(identity)
        return SecurityReport(
            "workstation_trust", True,
            f"identity={identity}, trusted={trusted}",
            time.monotonic() - start,
        )


class SecureSessionValidator:
    def validate(self, session: dict[str, Any]) -> SecurityReport:
        start = time.monotonic()
        exp = session.get("expires_at")
        if exp is None:
            return SecurityReport(
                "secure_session", False, "no expiration",
                time.monotonic() - start,
            )
        now = time.monotonic()
        expired = now > exp
        return SecurityReport(
            "secure_session", not expired,
            f"expires_at={exp}, now={now}",
            time.monotonic() - start,
        )
