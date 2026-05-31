from __future__ import annotations

from pathlib import Path

from app.core.stress.power_failure import PowerFailureValidator


class TestForcedShutdownWalWrite:
    def test_forced_shutdown(self, tmp_path: Path):
        v = PowerFailureValidator(tmp_path)
        r = v.validate_forced_shutdown_wal_write()
        assert r.passed, r.detail


class TestInterruptedCheckpointReplay:
    def test_interrupted_ckpt(self, tmp_path: Path):
        v = PowerFailureValidator(tmp_path)
        r = v.validate_interrupted_checkpoint_replay()
        assert r.passed, r.detail


class TestUnsafePowerLoss:
    def test_power_loss(self, tmp_path: Path):
        v = PowerFailureValidator(tmp_path)
        r = v.validate_unsafe_power_loss()
        assert r.passed, r.detail


class TestQueueReplayInterruption:
    def test_queue_interrupt(self, tmp_path: Path):
        v = PowerFailureValidator(tmp_path)
        r = v.validate_queue_replay_interruption()
        assert r.passed, r.detail


class TestArchiveReplayInterruption:
    def test_archive_interrupt(self, tmp_path: Path):
        v = PowerFailureValidator(tmp_path)
        r = v.validate_archive_replay_interruption()
        assert r.passed, r.detail


class TestRecoveryLoop:
    def test_recovery_loop(self, tmp_path: Path):
        v = PowerFailureValidator(tmp_path)
        r = v.validate_recovery_loop()
        assert r.passed, r.detail


class TestRollbackContinuityReplay:
    def test_rollback_continuity(self, tmp_path: Path):
        v = PowerFailureValidator(tmp_path)
        r = v.validate_rollback_continuity_replay()
        assert r.passed, r.detail


class TestPartialWriteRecovery:
    def test_partial_write(self, tmp_path: Path):
        v = PowerFailureValidator(tmp_path)
        r = v.validate_partial_write_recovery()
        assert r.passed, r.detail


class TestStartupRepairContinuity:
    def test_startup_repair(self, tmp_path: Path):
        v = PowerFailureValidator(tmp_path)
        r = v.validate_startup_repair_continuity()
        assert r.passed, r.detail


class TestDeterministicCrashReplay:
    def test_deterministic_crash(self, tmp_path: Path):
        v = PowerFailureValidator(tmp_path)
        r = v.validate_deterministic_crash_replay()
        assert r.passed, r.detail


class TestValidateAll:
    def test_all_power_failure(self, tmp_path: Path):
        v = PowerFailureValidator(tmp_path)
        results = v.validate_all()
        assert len(results) == 10
        passed = sum(1 for r in results if r.passed)
        assert passed >= 9, f"passed={passed}/10: {[r.scenario for r in results if not r.passed]}"

    def test_each_has_duration(self, tmp_path: Path):
        v = PowerFailureValidator(tmp_path)
        for r in v.validate_all():
            assert r.duration_seconds >= 0
