from __future__ import annotations

from app.core.chaos.federation_validator import OfflineFederationValidator


class TestLanInterruption:
    def test_node_park_unpark(self):
        v = OfflineFederationValidator()
        report = v.simulate_lan_interruption()
        assert report.success
        assert report.resolved

    def test_message_exchange(self):
        v = OfflineFederationValidator()
        report = v.simulate_lan_interruption()
        assert "node_a" in report.detail


class TestUsbSync:
    def test_manifest_creation(self):
        v = OfflineFederationValidator()
        report = v.simulate_usb_sync()
        assert report.success

    def test_replay_merges(self):
        v = OfflineFederationValidator()
        report = v.simulate_usb_sync()
        assert report.resolved


class TestDuplicateReplay:
    def test_dedup_detected(self):
        v = OfflineFederationValidator()
        report = v.simulate_duplicate_replay()
        assert report.resolved

    def test_resolution_works(self):
        v = OfflineFederationValidator()
        report = v.simulate_duplicate_replay()
        assert "dedup=False" in report.detail


class TestDelayedSync:
    def test_eventual_consistency(self):
        v = OfflineFederationValidator()
        report = v.simulate_delayed_sync(300.0)
        assert report.success

    def test_delay_metadata(self):
        v = OfflineFederationValidator()
        report = v.simulate_delayed_sync(600.0)
        assert "600" in report.detail


class TestNodeCollision:
    def test_first_wins(self):
        v = OfflineFederationValidator()
        report = v.simulate_node_identity_collision()
        assert report.success
        assert "original" in report.detail

    def test_collision_rejected(self):
        v = OfflineFederationValidator()
        report = v.simulate_node_identity_collision()
        assert "first=original" in report.detail
        assert "second=original" in report.detail


class TestDeterministicConflict:
    def test_same_nonce_resolves(self):
        v = OfflineFederationValidator()
        report = v.simulate_deterministic_conflict_replay("abc")
        assert report.success

    def test_different_nonce_consistent(self):
        v = OfflineFederationValidator()
        report = v.simulate_deterministic_conflict_replay("xyz")
        assert report.success


class TestOfflineQueueReplay:
    def test_queue_drained(self):
        v = OfflineFederationValidator()
        report = v.simulate_offline_queue_replay()
        assert report.success

    def test_pre_post_state(self):
        v = OfflineFederationValidator()
        report = v.simulate_offline_queue_replay()
        assert "queued=2" in report.detail


class TestFederationAudit:
    def test_append_only(self):
        v = OfflineFederationValidator()
        report = v.simulate_federation_audit_continuity()
        assert report.success

    def test_nodes_counted(self):
        v = OfflineFederationValidator()
        report = v.simulate_federation_audit_continuity()
        assert "nodes=3" in report.detail
