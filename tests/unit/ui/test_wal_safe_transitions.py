from __future__ import annotations

from app.ui.core.wal_safe_transitions import (
    TransitionVerdict,
    WalSafeTransitionCoordinator,
    WalState,
)


class TestWalSafeTransitionCoordinator:
    def test_initial_state_healthy(self):
        coord = WalSafeTransitionCoordinator()
        assert coord.wal_state == WalState.HEALTHY

    def test_healthy_allows_transition(self):
        coord = WalSafeTransitionCoordinator()
        result = coord.can_transition("dashboard", "letter_editor")
        assert result == TransitionVerdict.ALLOWED

    def test_corrupted_blocks_all(self):
        coord = WalSafeTransitionCoordinator()
        coord.set_wal_state(WalState.CORRUPTED)
        result = coord.can_transition("dashboard", "letter_editor")
        assert result == TransitionVerdict.BLOCKED

    def test_unknown_blocks_all(self):
        coord = WalSafeTransitionCoordinator()
        coord.set_wal_state(WalState.UNKNOWN)
        assert coord.can_transition("a", "b") == TransitionVerdict.BLOCKED

    def test_recovering_defers_normal_screens(self):
        coord = WalSafeTransitionCoordinator()
        coord.set_wal_state(WalState.RECOVERING)
        result = coord.can_transition("dashboard", "letter_editor")
        assert result == TransitionVerdict.DEFERRED

    def test_recovering_blocks_wal_screens(self):
        coord = WalSafeTransitionCoordinator()
        coord.set_wal_state(WalState.RECOVERING)
        for screen in coord.WAL_BLOCKED_SCREENS:
            assert coord.can_transition("dashboard", screen) == TransitionVerdict.BLOCKED

    def test_checkpointing_defers_wal_screens(self):
        coord = WalSafeTransitionCoordinator()
        coord.set_wal_state(WalState.CHECKPOINTING)
        for screen in coord.WAL_BLOCKED_SCREENS:
            assert coord.can_transition("dashboard", screen) == TransitionVerdict.DEFERRED

    def test_checkpointing_allows_normal_screens(self):
        coord = WalSafeTransitionCoordinator()
        coord.set_wal_state(WalState.CHECKPOINTING)
        result = coord.can_transition("dashboard", "letter_editor")
        assert result == TransitionVerdict.ALLOWED

    def test_record_transition(self):
        coord = WalSafeTransitionCoordinator()
        coord.record_transition("a", "b", blocked=True, reason="test")
        assert len(coord.transition_history) == 1
        assert coord.transition_history[0].is_blocked

    def test_blocked_count(self):
        coord = WalSafeTransitionCoordinator()
        coord.record_transition("a", "b", blocked=True)
        coord.record_transition("c", "d", blocked=False)
        assert coord.blocked_count == 1

    def test_before_transition_callback(self):
        coord = WalSafeTransitionCoordinator()
        coord.set_before_transition(lambda f, t: TransitionVerdict.BLOCKED)
        result = coord.can_transition("a", "b")
        assert result == TransitionVerdict.BLOCKED

    def test_reset(self):
        coord = WalSafeTransitionCoordinator()
        coord.set_wal_state(WalState.CORRUPTED)
        coord.record_transition("a", "b")
        coord.reset()
        assert coord.wal_state == WalState.HEALTHY
        assert len(coord.transition_history) == 0

    def test_set_wal_state(self):
        coord = WalSafeTransitionCoordinator()
        for state in WalState:
            coord.set_wal_state(state)
            assert coord.wal_state == state
