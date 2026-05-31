from __future__ import annotations

from app.ui.core.alert_service import AlertCategory, AlertService, AlertSeverity
from app.ui.core.safety_dialogs import (
    RollbackConfirmation,
    SafetyDialogService,
    UnsafeOperationGuard,
    UnsafeOperationSeverity,
)


class TestUnsafeOperationGuard:
    def test_default_blocking(self):
        guard = UnsafeOperationGuard(guard_id="g1")
        assert guard.should_block()

    def test_non_blocking(self):
        guard = UnsafeOperationGuard(guard_id="g1", blocking=False)
        assert not guard.should_block()

    def test_cooldown_blocks(self):
        guard = UnsafeOperationGuard(guard_id="g1", cooldown_seconds=10)
        assert guard.should_block()

    def test_record_trigger(self):
        guard = UnsafeOperationGuard(guard_id="g1")
        guard.record_trigger()
        assert guard.trigger_count == 1
        assert guard.last_triggered is not None


class TestRollbackConfirmation:
    def test_default_severity(self):
        rc = RollbackConfirmation(operation_id="op1", title="Delete")
        assert rc.severity == UnsafeOperationSeverity.MEDIUM

    def test_is_critical(self):
        rc = RollbackConfirmation(operation_id="op1", severity=UnsafeOperationSeverity.CRITICAL)
        assert rc.is_critical

    def test_not_critical(self):
        rc = RollbackConfirmation(operation_id="op1", severity=UnsafeOperationSeverity.LOW)
        assert not rc.is_critical


class TestSafetyDialogService:
    def test_register_guard(self):
        svc = SafetyDialogService()
        guard = UnsafeOperationGuard(guard_id="g1")
        svc.register_guard(guard)
        assert svc.get_guard("g1") is guard

    def test_check_operation_no_guard(self):
        svc = SafetyDialogService()
        assert svc.check_operation("nonexistent")

    def test_check_operation_blocked(self):
        svc = SafetyDialogService()
        svc.register_guard(UnsafeOperationGuard(guard_id="g1"))
        assert not svc.check_operation("g1")

    def test_check_operation_handler_bypass(self):
        svc = SafetyDialogService()
        svc.register_guard(UnsafeOperationGuard(guard_id="g1", handler=lambda: True))
        assert svc.check_operation("g1")

    def test_request_confirmation(self):
        svc = SafetyDialogService()
        rc = RollbackConfirmation(operation_id="op1", title="Confirm")
        assert svc.request_confirmation(rc)

    def test_pending_confirmations(self):
        svc = SafetyDialogService()
        svc.request_confirmation(RollbackConfirmation(operation_id="op1"))
        assert len(svc.pending_confirmations) == 1

    def test_resolve_confirmation_accepted(self):
        svc = SafetyDialogService()
        svc.request_confirmation(RollbackConfirmation(operation_id="op1"))
        result = svc.resolve_confirmation("op1", True)
        assert result is True
        assert len(svc.pending_confirmations) == 0

    def test_clear(self):
        svc = SafetyDialogService()
        svc.register_guard(UnsafeOperationGuard(guard_id="g1"))
        svc.request_confirmation(RollbackConfirmation(operation_id="op1"))
        svc.clear()
        assert len(svc.pending_confirmations) == 0
        assert svc.get_guard("g1") is None


class TestAlertService:
    def test_initial_state(self):
        svc = AlertService()
        assert svc.alert_count == 0

    def test_push_alert(self):
        svc = AlertService()
        alert = svc.create_alert(
            AlertCategory.SYSTEM_ERROR, "Error",
            "Something failed", AlertSeverity.ERROR,
        )
        assert svc.alert_count == 1
        assert alert.title == "Error"

    def test_acknowledge(self):
        svc = AlertService()
        alert = svc.create_alert(AlertCategory.SYSTEM_ERROR, "E", "M")
        assert svc.acknowledge(alert.alert_id)
        assert alert.acknowledged

    def test_acknowledge_all(self):
        svc = AlertService()
        svc.create_alert(AlertCategory.SYSTEM_ERROR, "E1", "M1")
        svc.create_alert(AlertCategory.SYSTEM_ERROR, "E2", "M2")
        assert svc.acknowledge_all() == 2

    def test_unacknowledged(self):
        svc = AlertService()
        svc.create_alert(AlertCategory.SYSTEM_ERROR, "E", "M")
        assert len(svc.unacknowledged) == 1

    def test_critical_alerts(self):
        svc = AlertService()
        svc.create_alert(AlertCategory.CORRUPTION, "Critical!", "Corrupt", AlertSeverity.CRITICAL)
        assert len(svc.critical_alerts) == 1

    def test_get_by_category(self):
        svc = AlertService()
        svc.create_alert(AlertCategory.WAL_RECOVERY, "WAL", "Issue")
        assert len(svc.get_by_category(AlertCategory.WAL_RECOVERY)) == 1

    def test_clear_acknowledged(self):
        svc = AlertService()
        a1 = svc.create_alert(AlertCategory.SYSTEM_ERROR, "E1", "M1")
        svc.create_alert(AlertCategory.SYSTEM_ERROR, "E2", "M2")
        svc.acknowledge(a1.alert_id)
        assert svc.clear_acknowledged() == 1

    def test_recent(self):
        svc = AlertService()
        for i in range(5):
            svc.create_alert(AlertCategory.SYSTEM_ERROR, f"E{i}", f"M{i}")
        assert len(svc.recent(3)) == 3

    def test_corruption_warning(self):
        svc = AlertService()
        alert = svc.corruption_warning("archive_index")
        assert alert.category == AlertCategory.CORRUPTION
        assert alert.severity == AlertSeverity.CRITICAL

    def test_wal_recovery_alert(self):
        svc = AlertService()
        alert = svc.wal_recovery_alert("WAL checkpoint failed")
        assert alert.category == AlertCategory.WAL_RECOVERY
        assert alert.severity == AlertSeverity.WARNING

    def test_sync_conflict_alert(self):
        svc = AlertService()
        alert = svc.sync_conflict_alert("Conflict detected")
        assert alert.category == AlertCategory.SYNC_CONFLICT

    def test_memory_pressure_alert(self):
        svc = AlertService()
        alert = svc.memory_pressure_alert(800.0, 1024)
        assert alert.category == AlertCategory.MEMORY_PRESSURE

    def test_safe_mode_alert(self):
        svc = AlertService()
        alert = svc.safe_mode_alert("Startup checks failed")
        assert alert.category == AlertCategory.SAFE_MODE

    def test_max_alerts_prunes(self):
        svc = AlertService()
        svc.MAX_ALERTS = 5
        for i in range(10):
            svc.create_alert(AlertCategory.SYSTEM_ERROR, f"E{i}", f"M{i}")
        assert svc.alert_count == 5

    def test_clear_all(self):
        svc = AlertService()
        svc.create_alert(AlertCategory.SYSTEM_ERROR, "E", "M")
        svc.clear_all()
        assert svc.alert_count == 0
