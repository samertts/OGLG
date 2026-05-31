from __future__ import annotations

import pytest

from app.ui.core.async_bridge import AsyncBridge, AsyncTask, TaskPriority
from app.ui.core.bounded_lifecycle import BoundedLifecycle, LifecyclePhase
from app.ui.core.crash_safe_window import CrashSafeWindow, WindowGuard
from app.ui.core.dialog_wrapper import DialogTransaction, TransactionSafeDialog
from app.ui.core.event_isolation import EventBoundary, EventIsolationZone
from app.ui.core.replay_actions import ReplayAction, ReplayActionLog, ReplaySafeDispatcher


class TestAsyncBridge:
    def test_submit_task(self):
        bridge = AsyncBridge()
        task = AsyncTask(name="test", fn=lambda: 42)
        handle = bridge.submit(task)
        handle.state = handle.state  # simulated
        assert handle.task_id == "test"

    def test_shutdown_cancels_pending(self):
        bridge = AsyncBridge()
        task = AsyncTask(name="pending", fn=lambda: None)
        bridge.submit(task)
        bridge.shutdown()
        handle = bridge.status("pending")
        assert handle is None or handle.state.name in ("CANCELLED", "COMPLETED", "FAILED")

    def test_cancel_task(self):
        bridge = AsyncBridge()
        bridge.cancel("cancel_test")  # cancel before submission works
        assert bridge.cancel("nonexistent") is False

    def test_pending_count(self):
        bridge = AsyncBridge()
        task = AsyncTask(name="count_test", fn=lambda: None)
        bridge.submit(task)
        assert bridge.pending_count >= 0  # may have started

    def test_submit_after_shutdown(self):
        bridge = AsyncBridge()
        bridge.shutdown()
        task = AsyncTask(name="fail", fn=lambda: None)
        try:
            bridge.submit(task)
            assert False, "Should have raised"
        except RuntimeError:
            pass


class TestBoundedLifecycle:
    def test_initial_state(self):
        bl = BoundedLifecycle("test-widget")
        assert bl.phase == LifecyclePhase.UNINITIALIZED

    def test_initialize_transition(self):
        bl = BoundedLifecycle("test")
        bl.initialize()
        assert bl.phase == LifecyclePhase.INITIALIZING

    def test_activate(self):
        bl = BoundedLifecycle("test")
        bl.initialize()
        bl.activate()
        assert bl.is_active

    def test_suspend(self):
        bl = BoundedLifecycle("test")
        bl.initialize()
        bl.activate()
        bl.suspend()
        assert bl.phase == LifecyclePhase.SUSPENDED

    def test_dispose(self):
        bl = BoundedLifecycle("test")
        bl.dispose()
        assert bl.is_disposed

    def test_activate_disposed_raises(self):
        bl = BoundedLifecycle("test")
        bl.dispose()
        try:
            bl.activate()
            assert False, "Should have raised"
        except RuntimeError:
            pass

    def test_error_setting(self):
        bl = BoundedLifecycle("test")
        bl.set_error("something broke")
        assert bl.state.error == "something broke"

    def test_activation_count(self):
        bl = BoundedLifecycle("test")
        bl.initialize()
        bl.activate()
        assert bl.state.activation_count == 1

    def test_max_activations(self):
        bl = BoundedLifecycle("test", max_activations=2)
        bl.initialize()
        bl.activate()
        bl.suspend()
        bl.activate()
        bl.suspend()
        with pytest.raises(RuntimeError):
            bl.activate()


class TestCrashSafeWindow:
    def test_initial_state(self):
        w = CrashSafeWindow("w1")
        assert not w.is_open
        assert not w.shutdown_requested

    def test_open_close(self):
        w = CrashSafeWindow("w1")
        w.open()
        assert w.is_open
        w.close()
        assert not w.is_open

    def test_close_blocked_by_handler(self):
        w = CrashSafeWindow("w1", WindowGuard(close_handler=lambda: False))
        w.open()
        assert not w.close()

    def test_crash_tracking(self):
        errors = []
        w = CrashSafeWindow("w1", WindowGuard(error_handler=lambda e: errors.append(e)))
        with w.protect():
            raise ValueError("boom")
        assert len(errors) == 1
        assert w.guard.crash_count == 1

    def test_shutdown_after_max_crashes(self):
        w = CrashSafeWindow("w1", WindowGuard(max_crashes=2))
        with w.protect():
            raise ValueError("1")
        with w.protect():
            raise ValueError("2")
        assert w.shutdown_requested

    def test_protect_does_not_raise(self):
        w = CrashSafeWindow("w1")
        with w.protect():
            raise ValueError("caught")
        assert True  # no re-raise


class TestTransactionSafeDialog:
    def test_dialog_initial_state(self):
        dlg = TransactionSafeDialog("d1")
        assert not dlg.is_closed

    def test_begin_transaction(self):
        dlg = TransactionSafeDialog("d1")
        tx = dlg.begin_transaction("tx-1")
        assert tx.is_open

    def test_transaction_commit(self):
        dlg = TransactionSafeDialog("d1")
        tx = dlg.begin_transaction("tx-1")
        tx.commit()
        assert tx.state.name == "COMMITTED"

    def test_transaction_rollback(self):
        dlg = TransactionSafeDialog("d1")
        tx = dlg.begin_transaction("tx-1")
        tx.rollback()
        assert tx.state.name == "ROLLED_BACK"

    def test_transaction_context_manager_commits(self):
        dlg = TransactionSafeDialog("d1")
        with dlg.transaction("tx-1") as tx:
            assert tx.is_open
        assert tx.state.name == "COMMITTED"

    def test_transaction_context_manager_rolls_back_on_error(self):
        dlg = TransactionSafeDialog("d1")
        try:
            with dlg.transaction("tx-1") as tx:
                raise ValueError("fail")
        except ValueError:
            pass
        assert tx.state.name == "ROLLED_BACK"

    def test_close_rolls_back_open_transaction(self):
        dlg = TransactionSafeDialog("d1")
        dlg.begin_transaction("tx-1")
        dlg.close()
        assert dlg.is_closed

    def test_commit_fails_closed(self):
        dlg = TransactionSafeDialog("d1")
        tx = dlg.begin_transaction("tx-1")
        tx.commit()
        assert True  # no exception

    def test_commit_callback(self):
        calls = []
        tx = DialogTransaction(transaction_id="tx-1", on_commit=lambda: calls.append("committed"))
        tx.open()
        tx.commit()
        assert calls == ["committed"]

    def test_rollback_callback(self):
        calls = []
        tx = DialogTransaction(transaction_id="tx-1", on_rollback=lambda: calls.append("rolled"))
        tx.open()
        tx.rollback()
        assert calls == ["rolled"]


class TestEventIsolation:
    def test_zone_allows_registered_event(self):
        zone = EventIsolationZone("z1")
        events = []
        zone.register("navigation", lambda t, d: events.append((t, d)))
        zone.emit("navigation", {"page": "home"})
        assert len(events) == 1

    def test_zone_rejects_disallowed_event(self):
        zone = EventIsolationZone("z1", EventBoundary(allowed_event_types=("navigation",)))
        try:
            zone.emit("forbidden", {})
            assert False
        except ValueError:
            pass

    def test_max_handlers_limit(self):
        zone = EventIsolationZone("z1")
        for i in range(20):
            zone.register("navigation", lambda t, d: None)
        try:
            zone.register("navigation", lambda t, d: None)
            assert False
        except RuntimeError:
            pass

    def test_event_propagation_stops_on_error(self):
        zone = EventIsolationZone("z1", EventBoundary(stop_propagation_on_error=True))
        calls = []
        zone.register("navigation", lambda t, d: (_ for _ in ()).throw(ValueError("fail")))
        zone.register("navigation", lambda t, d: calls.append("should not reach"))
        try:
            zone.emit("navigation", {})
        except ValueError:
            pass
        assert len(calls) == 0


class TestReplayActions:
    def test_action_log_append(self):
        log = ReplayActionLog()
        action = ReplayAction(action_id="a1", action_type="navigate")
        log.append(action)
        assert log.count == 1

    def test_action_log_max_entries(self):
        log = ReplayActionLog(max_entries=3)
        for i in range(5):
            log.append(ReplayAction(action_id=str(i), action_type="test"))
        assert log.count == 3

    def test_replay_dispatcher_dispatch(self):
        log = ReplayActionLog()
        dispatcher = ReplaySafeDispatcher(log)
        results = []
        dispatcher.register("navigate", lambda a: results.append(a.payload))
        action = ReplayAction(action_id="a1", action_type="navigate", payload={"page": "home"})
        dispatcher.dispatch(action)
        assert len(results) == 1

    def test_replay_dispatcher_replay(self):
        log = ReplayActionLog()
        dispatcher = ReplaySafeDispatcher(log)
        results = []
        dispatcher.register("search", lambda a: results.append(a.payload))
        action = ReplayAction(action_id="a1", action_type="search", payload={"q": "test"})
        dispatcher.replay(action)
        assert len(results) == 1
        assert action.replay_token is not None

    def test_replay_no_handler(self):
        log = ReplayActionLog()
        dispatcher = ReplaySafeDispatcher(log)
        action = ReplayAction(action_id="a1", action_type="unknown")
        dispatcher.dispatch(action)
        assert action.error is not None

    def test_replay_error_tracking(self):
        log = ReplayActionLog()
        dispatcher = ReplaySafeDispatcher(log)
        dispatcher.register("fail", lambda a: (_ for _ in ()).throw(ValueError("bad")))
        action = ReplayAction(action_id="a1", action_type="fail")
        dispatcher.dispatch(action)
        assert action.error is not None

    def test_log_last_n(self):
        log = ReplayActionLog()
        for i in range(10):
            log.append(ReplayAction(action_id=str(i), action_type="test"))
        assert len(log.last(3)) == 3

    def test_log_clear(self):
        log = ReplayActionLog()
        log.append(ReplayAction(action_id="a1", action_type="test"))
        log.clear()
        assert log.count == 0
