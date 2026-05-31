from __future__ import annotations

import pytest

from app.ui.contracts.memory import MemoryContract, MemoryScope
from app.ui.contracts.rendering import BoundedRender, RenderGuard
from app.ui.contracts.rtl import RtlAlignment, RtlContract
from app.ui.contracts.state_boundaries import BoundedState, StateBoundary
from app.ui.contracts.workflow import AsyncWorkflow, WorkflowContext, WorkflowState


class TestWorkflowContracts:
    def test_workflow_initial_state(self):
        wf = AsyncWorkflow(workflow_id="wf-1", name="test")
        assert wf.state == WorkflowState.PENDING
        assert not wf.is_terminal()

    def test_workflow_terminal_states(self):
        wf = AsyncWorkflow(workflow_id="wf-1", name="test")
        wf.state = WorkflowState.COMPLETED
        assert wf.is_terminal()

    def test_workflow_can_transition_valid(self):
        wf = AsyncWorkflow(workflow_id="wf-1", name="test")
        assert wf.can_transition_to(WorkflowState.RUNNING)
        assert wf.can_transition_to(WorkflowState.CANCELLED)

    def test_workflow_can_transition_invalid(self):
        wf = AsyncWorkflow(workflow_id="wf-1", name="test")
        assert not wf.can_transition_to(WorkflowState.COMPLETED)

    def test_workflow_context_holds_metadata(self):
        ctx = WorkflowContext(
            workflow=AsyncWorkflow(workflow_id="wf-1", name="test"),
            caller_id="user-1",
            audit_token="audit-1",
        )
        assert ctx.caller_id == "user-1"
        assert ctx.audit_token == "audit-1"

    def test_workflow_rollback_transition(self):
        wf = AsyncWorkflow(workflow_id="wf-1", name="test")
        wf.state = WorkflowState.RUNNING
        assert wf.can_transition_to(WorkflowState.ROLLED_BACK)
        wf.state = WorkflowState.ROLLED_BACK
        assert wf.is_terminal()

    def test_terminal_blocks_transitions(self):
        wf = AsyncWorkflow(workflow_id="wf-1", name="test")
        wf.state = WorkflowState.COMPLETED
        assert not wf.can_transition_to(WorkflowState.RUNNING)

    def test_failed_transition(self):
        wf = AsyncWorkflow(workflow_id="wf-1", name="test")
        wf.state = WorkflowState.RUNNING
        assert wf.can_transition_to(WorkflowState.FAILED)

    def test_progress_tracking(self):
        wf = AsyncWorkflow(workflow_id="wf-1", name="test")
        wf.progress = 0.5
        assert wf.progress == 0.5

    def test_error_message(self):
        wf = AsyncWorkflow(workflow_id="wf-1", name="test")
        wf.state = WorkflowState.FAILED
        wf.error_message = "Task failed"
        assert wf.error_message == "Task failed"


class TestStateBoundaries:
    def test_state_boundary_validates_primitives(self):
        boundary = StateBoundary()
        assert boundary.validate("hello")
        assert boundary.validate(42)
        assert boundary.validate(True)

    def test_state_boundary_rejects_long_string(self):
        boundary = StateBoundary(max_string_length=10)
        assert not boundary.validate("x" * 11)

    def test_state_boundary_rejects_deep_nesting(self):
        boundary = StateBoundary(max_nesting_depth=1)
        assert not boundary.validate([[[[]]]])

    def test_bounded_state_initialization(self):
        bs = BoundedState(initial=42)
        assert bs.value == 42

    def test_bounded_state_rejects_invalid(self):
        boundary = StateBoundary(max_string_length=5)
        bs = BoundedState(initial="ok", boundary=boundary)
        with pytest.raises(ValueError):
            bs.value = "too long"

    def test_bounded_state_rejects_bad_initial(self):
        boundary = StateBoundary(forbid_none=True)
        with pytest.raises(ValueError):
            BoundedState(initial=None, boundary=boundary)

    def test_boundary_rejects_unsupported_types(self):
        boundary = StateBoundary()
        assert not boundary.validate(bytearray(b"test"))


class TestRenderingContracts:
    def test_bounded_render_defaults(self):
        br = BoundedRender()
        assert br.within_bounds(50, 5)

    def test_bounded_render_rejects(self):
        br = BoundedRender(max_widgets=10, max_depth=3)
        assert not br.within_bounds(20, 5)

    def test_render_guard_protects_ok(self):
        guard = RenderGuard()
        with guard.protect():
            pass

    def test_render_guard_catches_error(self):
        errors = []
        guard = RenderGuard(on_crash=lambda e: errors.append(e))
        with guard.protect():
            raise ValueError("test crash")
        assert len(errors) == 1

    def test_render_guard_depth_limit(self):
        guard = RenderGuard()
        with guard.protect():
            pass
        assert guard._depth == 0

    def test_render_guard_reset(self):
        guard = RenderGuard()
        guard._depth = 10
        guard.reset_depth()
        assert guard._depth == 0


class TestRtlContracts:
    def test_rtl_default_enabled(self):
        rtl = RtlContract()
        assert rtl.enabled

    def test_rtl_locale_detection(self):
        rtl = RtlContract()
        assert rtl.is_rtl_locale("ar")
        assert rtl.is_rtl_locale("ar_SA")
        assert not rtl.is_rtl_locale("en_US")

    def test_rtl_text_direction(self):
        rtl = RtlContract()
        result = rtl.apply_text_direction("مرحبا")
        assert result["direction"] == "rtl"

    def test_ltr_text_direction(self):
        rtl = RtlContract()
        result = rtl.apply_text_direction("Hello")
        assert result["direction"] == "ltr"

    def test_sanitize_html_rtl(self):
        rtl = RtlContract()
        html = "<html><body>Test</body></html>"
        result = rtl.sanitize_html_rtl(html)
        assert 'dir="rtl"' in result

    def test_sanitize_html_ltr(self):
        rtl = RtlContract(enabled=False)
        html = "<html><body>Test</body></html>"
        result = rtl.sanitize_html_rtl(html)
        assert 'dir="ltr"' in result

    def test_alignment_default(self):
        rtl = RtlContract()
        assert rtl.alignment == RtlAlignment.RIGHT


class TestMemoryContracts:
    def test_memory_default_limits(self):
        mc = MemoryContract()
        assert mc.within_limit(MemoryScope.SEARCH_RESULTS, 100)

    def test_memory_limit_exceeded(self):
        mc = MemoryContract(max_search_results=50)
        assert not mc.within_limit(MemoryScope.SEARCH_RESULTS, 100)

    def test_memory_scope_returns_limit(self):
        mc = MemoryContract()
        assert mc.limit_for(MemoryScope.WIDGET_CACHE) == 50 * 1024 * 1024

    def test_memory_unknown_scope(self):
        mc = MemoryContract()
        assert mc.limit_for(MemoryScope.RENDER_QUEUE) == 100

    def test_memory_zero_limit_ok(self):
        mc = MemoryContract(scope_limits={MemoryScope.SEARCH_RESULTS: 0})
        assert mc.within_limit(MemoryScope.SEARCH_RESULTS, 9999)

    def test_custom_scope_limit(self):
        mc = MemoryContract(scope_limits={MemoryScope.DRAFT_STATE: 256})
        assert mc.limit_for(MemoryScope.DRAFT_STATE) == 256
