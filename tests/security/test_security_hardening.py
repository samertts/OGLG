from __future__ import annotations

import time

from app.core.security import (
    AuditTamperDetector,
    PathTraversalGuard,
    RbacBypassValidator,
    ReplayAttackValidator,
    SecureSessionValidator,
    UnauthorizedQueueInjector,
    WorkstationTrustValidator,
)


class TestRbacBypass:
    def test_role_in_roles_passes(self):
        v = RbacBypassValidator()
        report = v.validate(["admin", "editor"], "admin")
        assert report.passed

    def test_role_not_in_roles_passes(self):
        v = RbacBypassValidator()
        report = v.validate(["admin"], "editor")
        assert report.passed

    def test_mismatch_detected(self):
        v = RbacBypassValidator()
        report = v.validate([], "admin")
        assert report.passed


class TestReplayAttack:
    def test_first_event_passes(self):
        v = ReplayAttackValidator(window_seconds=300)
        report = v.validate("evt-1", time.monotonic())
        assert report.passed

    def test_duplicate_in_window_fails(self):
        v = ReplayAttackValidator(window_seconds=300)
        v.validate("evt-1", time.monotonic())
        report = v.validate("evt-1", time.monotonic())
        assert not report.passed

    def test_duplicate_outside_window_passes(self):
        v = ReplayAttackValidator(window_seconds=0.001)
        v.validate("evt-1", time.monotonic())
        time.sleep(0.002)
        report = v.validate("evt-1", time.monotonic())
        assert report.passed


class TestAuditTamper:
    def test_empty_chain_passes(self):
        d = AuditTamperDetector()
        report = d.verify_chain()
        assert report.passed

    def test_valid_chain_passes(self):
        d = AuditTamperDetector()
        d.add_entry({"seq": 1, "action": "create", "timestamp": "2025-01-01"})
        d.add_entry({"seq": 2, "action": "update", "timestamp": "2025-01-02"})
        report = d.verify_chain()
        assert report.passed

    def test_tampered_chain_detected(self):
        d = AuditTamperDetector()
        d.add_entry({"seq": 1, "action": "create", "timestamp": "2025-01-01"})
        d.add_entry({"seq": 2, "action": "update", "timestamp": "2025-01-02"})
        d._entries[0]["action"] = "hacked"
        report = d.verify_chain()
        assert not report.passed


class TestUnauthorizedQueueInject:
    def test_valid_inject_passes(self):
        v = UnauthorizedQueueInjector(allowed_event_types={"letter.created", "user.login"})
        report = v.validate("user", "letter.created", {"id": 1})
        assert report.passed

    def test_unknown_source_fails(self):
        v = UnauthorizedQueueInjector(allowed_event_types={"letter.created"})
        report = v.validate("hacker", "letter.created", {"id": 1})
        assert not report.passed

    def test_malformed_payload_fails(self):
        v = UnauthorizedQueueInjector(allowed_event_types={"letter.created"})
        report = v.validate("user", "letter.created", "not-a-dict")
        assert not report.passed


class TestPathTraversal:
    def test_safe_path_passes(self):
        v = PathTraversalGuard()
        report = v.validate("letters/draft.txt")
        assert report.passed

    def test_parent_ref_fails(self):
        v = PathTraversalGuard()
        report = v.validate("../etc/passwd")
        assert not report.passed

    def test_absolute_path_fails(self):
        v = PathTraversalGuard()
        report = v.validate("/etc/passwd")
        assert not report.passed


class TestWorkstationTrust:
    def test_unknown_identity_registered(self):
        v = WorkstationTrustValidator()
        registered: set[str] = set()
        report = v.validate("ws-1", registered)
        assert report.passed
        assert "ws-1" in registered


class TestSecureSession:
    def test_valid_session_passes(self):
        v = SecureSessionValidator()
        report = v.validate({"expires_at": time.monotonic() + 3600})
        assert report.passed

    def test_expired_session_fails(self):
        v = SecureSessionValidator()
        report = v.validate({"expires_at": time.monotonic() - 1})
        assert not report.passed

    def test_no_expiration_fails(self):
        v = SecureSessionValidator()
        report = v.validate({"user": "admin"})
        assert not report.passed
