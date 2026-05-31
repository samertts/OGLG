from __future__ import annotations

from pathlib import Path

from app.core.stress.federation_recovery import FederationRecoveryValidator


class TestDelayedUsbSync:
    def test_usb_sync(self, tmp_path: Path):
        v = FederationRecoveryValidator(tmp_path)
        r = v.validate_delayed_usb_sync()
        assert r.passed, r.detail


class TestDuplicateReplayReconciliation:
    def test_dedup_replay(self, tmp_path: Path):
        v = FederationRecoveryValidator(tmp_path)
        r = v.validate_duplicate_replay_reconciliation()
        assert r.passed, r.detail


class TestNodeCollisionReplay:
    def test_collision(self, tmp_path: Path):
        v = FederationRecoveryValidator(tmp_path)
        r = v.validate_node_collision_replay()
        assert r.passed, r.detail


class TestInterruptedFederationRecovery:
    def test_interrupted_fed(self, tmp_path: Path):
        v = FederationRecoveryValidator(tmp_path)
        r = v.validate_interrupted_federation_recovery()
        assert r.passed, r.detail


class TestLowBandwidthReplayEndurance:
    def test_low_bw(self, tmp_path: Path):
        v = FederationRecoveryValidator(tmp_path)
        r = v.validate_low_bandwidth_replay_endurance()
        assert r.passed, r.detail


class TestQueueReconciliationReplay:
    def test_queue_recon(self, tmp_path: Path):
        v = FederationRecoveryValidator(tmp_path)
        r = v.validate_queue_reconciliation_replay()
        assert r.passed, r.detail


class TestAuditContinuityFederation:
    def test_audit_fed(self, tmp_path: Path):
        v = FederationRecoveryValidator(tmp_path)
        r = v.validate_audit_continuity_federation()
        assert r.passed, r.detail


class TestDeterministicConflictReplay:
    def test_conflict_replay(self, tmp_path: Path):
        v = FederationRecoveryValidator(tmp_path)
        r = v.validate_deterministic_conflict_replay()
        assert r.passed, r.detail


class TestBoundedRetryContinuity:
    def test_bounded_retry(self, tmp_path: Path):
        v = FederationRecoveryValidator(tmp_path)
        r = v.validate_bounded_retry_continuity()
        assert r.passed, r.detail


class TestOfflineRecovery:
    def test_offline_recovery(self, tmp_path: Path):
        v = FederationRecoveryValidator(tmp_path)
        r = v.validate_offline_recovery()
        assert r.passed, r.detail


class TestValidateAll:
    def test_all_federation(self, tmp_path: Path):
        v = FederationRecoveryValidator(tmp_path)
        results = v.validate_all()
        assert len(results) == 10
        passed = sum(1 for r in results if r.passed)
        assert passed >= 9, f"passed={passed}/10: {[r.scenario for r in results if not r.passed]}"

    def test_each_has_duration(self, tmp_path: Path):
        v = FederationRecoveryValidator(tmp_path)
        for r in v.validate_all():
            assert r.duration_seconds >= 0
