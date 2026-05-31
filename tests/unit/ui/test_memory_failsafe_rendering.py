from __future__ import annotations

from app.ui.contracts.memory import MemoryScope
from app.ui.core.memory_failsafe_rendering import (
    MemoryAwareRenderGate,
    create_memory_failsafe_renderer,
)


class TestMemoryAwareRenderGate:
    def test_initial_state(self):
        gate = MemoryAwareRenderGate()
        assert gate.pressure_level == "none"
        assert gate.render_blocked_count == 0

    def test_should_render_within_bounds(self):
        gate = MemoryAwareRenderGate()
        assert gate.should_render(10, 3)

    def test_should_not_render_exceeding_widgets(self):
        gate = MemoryAwareRenderGate()
        gate.render_bounds.max_widgets = 5
        assert not gate.should_render(10, 1)
        assert gate.render_blocked_count == 1

    def test_should_not_render_exceeding_depth(self):
        gate = MemoryAwareRenderGate()
        gate.render_bounds.max_depth = 2
        assert not gate.should_render(1, 10)
        assert gate.render_blocked_count == 1

    def test_critical_pressure_blocks_render(self):
        gate = MemoryAwareRenderGate()
        gate.update_pressure(960.0, 1000)
        assert gate.pressure_level == "critical"
        assert not gate.should_render(1, 1)
        assert gate.render_blocked_count == 1

    def test_high_pressure_allows_render(self):
        gate = MemoryAwareRenderGate()
        gate.update_pressure(870.0, 1000)
        assert gate.pressure_level == "high"
        assert gate.should_render(1, 1)
        assert gate.render_allowed_count == 1

    def test_update_pressure_ratio(self):
        gate = MemoryAwareRenderGate()
        gate.update_pressure(500.0, 1000)
        assert gate.pressure_level == "none"
        gate.update_pressure(860.0, 1000)
        assert gate.pressure_level == "high"
        gate.update_pressure(960.0, 1000)
        assert gate.pressure_level == "critical"

    def test_within_memory_limit(self):
        gate = MemoryAwareRenderGate()
        assert gate.within_memory_limit(MemoryScope.SEARCH_RESULTS, 100)
        assert not gate.within_memory_limit(MemoryScope.SEARCH_RESULTS, 9999)

    def test_scope_limit(self):
        gate = MemoryAwareRenderGate()
        assert gate.scope_limit(MemoryScope.WIDGET_CACHE) > 0

    def test_callback_notification(self):
        gate = MemoryAwareRenderGate()
        events: list[str] = []
        gate.register_callback(lambda e: events.append(e))
        gate.render_bounds.max_widgets = 0
        gate.should_render(10, 1)
        assert "render_blocked_bounds" in events

    def test_gate_context_manager_allowed(self):
        gate = MemoryAwareRenderGate()
        with gate.gate(1, 1) as allowed:
            assert allowed

    def test_gate_context_manager_blocked(self):
        gate = MemoryAwareRenderGate()
        gate.render_bounds.max_widgets = 0
        with gate.gate(10, 1) as allowed:
            assert not allowed

    def test_create_memory_failsafe_renderer(self):
        gate = create_memory_failsafe_renderer()
        assert isinstance(gate, MemoryAwareRenderGate)
        assert gate.render_bounds.max_widgets == 500

    def test_render_allowed_count(self):
        gate = MemoryAwareRenderGate()
        for _ in range(5):
            gate.should_render(1, 1)
        assert gate.render_allowed_count == 5
