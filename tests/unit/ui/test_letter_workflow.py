from __future__ import annotations

import pytest

from app.ui.core.approval_routing import ApprovalDecision, ApprovalRouter
from app.ui.core.archive_linker import ArchiveLinker
from app.ui.core.attachment_handler import AttachmentHandler, AttachmentState
from app.ui.core.letter_workflow import (
    CorrespondenceDraft,
    DraftManager,
    LetterState,
    NumberingPreview,
    WorkflowActionType,
)


class TestCorrespondenceDraft:
    def test_initial_state(self):
        draft = CorrespondenceDraft(letter_id="L-001")
        assert draft.state == LetterState.DRAFT
        assert not draft.has_unsaved_changes
        assert draft.version == 1

    def test_mark_dirty(self):
        draft = CorrespondenceDraft(letter_id="L-001")
        draft.mark_dirty()
        assert draft.has_unsaved_changes

    def test_mark_saved(self):
        draft = CorrespondenceDraft(letter_id="L-001")
        draft.mark_dirty()
        draft.mark_saved()
        assert not draft.has_unsaved_changes
        assert draft.version == 2


class TestDraftManager:
    def test_create_draft(self):
        dm = DraftManager()
        draft = dm.create_draft("L-001", subject="Test", body="Hello")
        assert draft.letter_id == "L-001"
        assert draft.subject == "Test"
        assert dm.draft_count == 1

    def test_get_draft(self):
        dm = DraftManager()
        dm.create_draft("L-001")
        draft = dm.get_draft("L-001")
        assert draft is not None

    def test_get_nonexistent_draft(self):
        dm = DraftManager()
        assert dm.get_draft("nonexistent") is None

    def test_update_draft(self):
        dm = DraftManager()
        dm.create_draft("L-001", subject="Old")
        dm.update_draft("L-001", subject="New")
        draft = dm.get_draft("L-001")
        assert draft is not None
        assert draft.subject == "New"

    def test_delete_draft(self):
        dm = DraftManager()
        dm.create_draft("L-001")
        assert dm.delete_draft("L-001") is True
        assert dm.draft_count == 0

    def test_submit_for_approval(self):
        dm = DraftManager()
        dm.create_draft("L-001")
        result = dm.submit_for_approval("L-001", "user-1")
        assert result is not None
        assert result.state == LetterState.PENDING_APPROVAL

    def test_submit_already_submitted(self):
        dm = DraftManager()
        dm.create_draft("L-001")
        dm.submit_for_approval("L-001", "user-1")
        result = dm.submit_for_approval("L-001", "user-2")
        assert result is None

    def test_max_drafts_limit(self):
        dm = DraftManager()
        dm.MAX_DRAFTS = 2
        dm.create_draft("L-001")
        dm.create_draft("L-002")
        with pytest.raises(RuntimeError):
            dm.create_draft("L-003")

    def test_action_log_on_create(self):
        dm = DraftManager()
        dm.create_draft("L-001")
        assert len(dm.action_log) == 1
        assert dm.action_log[0].action_type == WorkflowActionType.CREATE

    def test_action_log_on_submit(self):
        dm = DraftManager()
        dm.create_draft("L-001")
        dm.submit_for_approval("L-001", "user-1")
        assert len(dm.action_log) == 2

    def test_clear(self):
        dm = DraftManager()
        dm.create_draft("L-001")
        dm.clear()
        assert dm.draft_count == 0
        assert len(dm.action_log) == 0

    def test_subject_length_limit(self):
        dm = DraftManager()
        with pytest.raises(ValueError):
            dm.create_draft("L-001", subject="x" * 501)

    def test_draft_ids(self):
        dm = DraftManager()
        dm.create_draft("L-001")
        dm.create_draft("L-002")
        assert dm.draft_ids == ["L-001", "L-002"]


class TestNumberingPreview:
    def test_generate(self):
        np = NumberingPreview()
        np.generate(prefix="MIN", sequence=42, year=2026)
        assert np.full_number == "MIN-2026-0042"
        assert np.formatted == "MIN / 0042 / 2026"

    def test_default_year(self):
        np = NumberingPreview()
        np.generate(prefix="MOH", sequence=1)
        assert np.year > 0


class TestApprovalRouter:
    def test_create_route(self):
        router = ApprovalRouter()
        route = router.create_route("route-1", "Standard Approval")
        assert route.route_id == "route-1"

    def test_add_step(self):
        router = ApprovalRouter()
        route = router.create_route("route-1")
        route.add_step("manager", 1)
        route.add_step("director", 2)
        assert len(route.steps) == 2

    def test_approve_step(self):
        router = ApprovalRouter()
        route = router.create_route("route-1")
        step = route.add_step("manager", 1)
        result = router.decide_step("route-1", step.step_id, ApprovalDecision.APPROVED, "user-1")
        assert result
        assert step.decision == ApprovalDecision.APPROVED

    def test_all_approved(self):
        router = ApprovalRouter()
        route = router.create_route("route-1")
        s1 = route.add_step("manager", 1)
        s2 = route.add_step("director", 2)
        router.decide_step("route-1", s1.step_id, ApprovalDecision.APPROVED, "u1")
        router.decide_step("route-1", s2.step_id, ApprovalDecision.APPROVED, "u2")
        assert route.all_approved

    def test_any_rejected(self):
        router = ApprovalRouter()
        route = router.create_route("route-1")
        s1 = route.add_step("manager", 1)
        router.decide_step("route-1", s1.step_id, ApprovalDecision.REJECTED, "u1")
        assert route.any_rejected

    def test_delete_route(self):
        router = ApprovalRouter()
        router.create_route("route-1")
        assert router.delete_route("route-1") is True
        assert router.route_count == 0

    def test_clear(self):
        router = ApprovalRouter()
        router.create_route("route-1")
        router.clear()
        assert router.route_count == 0


class TestArchiveLinker:
    def test_link(self):
        linker = ArchiveLinker()
        link = linker.link("L-001", "ARC-001")
        assert link is not None
        assert link.letter_id == "L-001"

    def test_get_links(self):
        linker = ArchiveLinker()
        linker.link("L-001", "ARC-001")
        linker.link("L-001", "ARC-002")
        assert len(linker.get_links("L-001")) == 2

    def test_unlink(self):
        linker = ArchiveLinker()
        linker.link("L-001", "ARC-001")
        assert linker.unlink("L-001", "ARC-001") is True
        assert len(linker.get_links("L-001")) == 0

    def test_max_links(self):
        linker = ArchiveLinker(max_links=2)
        linker.link("L-001", "ARC-001")
        linker.link("L-002", "ARC-002")
        result = linker.link("L-003", "ARC-003")
        assert result is None

    def test_total_links(self):
        linker = ArchiveLinker()
        linker.link("L-001", "ARC-001")
        linker.link("L-002", "ARC-002")
        assert linker.total_links == 2

    def test_get_letters_for_archive_entry(self):
        linker = ArchiveLinker()
        linker.link("L-001", "ARC-001")
        linker.link("L-002", "ARC-001")
        letters = linker.get_letters_for_archive_entry("ARC-001")
        assert len(letters) == 2


class TestAttachmentHandler:
    def test_add_attachment(self):
        handler = AttachmentHandler()
        ref = handler.add_attachment("L-001", "ATT-001", "doc.pdf", "application/pdf", 1024)
        assert ref is not None
        assert ref.filename == "doc.pdf"

    def test_get_attachments(self):
        handler = AttachmentHandler()
        handler.add_attachment("L-001", "ATT-001", "doc.pdf")
        handler.add_attachment("L-001", "ATT-002", "img.png")
        assert len(handler.get_attachments("L-001")) == 2

    def test_remove_attachment(self):
        handler = AttachmentHandler()
        handler.add_attachment("L-001", "ATT-001", "doc.pdf")
        assert handler.remove_attachment("L-001", "ATT-001") is True
        assert len(handler.get_attachments("L-001")) == 0

    def test_mark_stored(self):
        handler = AttachmentHandler()
        handler.add_attachment("L-001", "ATT-001", "doc.pdf")
        assert handler.mark_stored("ATT-001", "abc123")
        ref = handler.get_attachments("L-001")[0]
        assert ref.state == AttachmentState.STORED
        assert ref.checksum == "abc123"

    def test_max_per_letter(self):
        handler = AttachmentHandler()
        handler.MAX_ATTACHMENTS_PER_LETTER = 2
        handler.add_attachment("L-001", "ATT-001", "a.pdf")
        handler.add_attachment("L-001", "ATT-002", "b.pdf")
        ref = handler.add_attachment("L-001", "ATT-003", "c.pdf")
        assert ref is None

    def test_max_total(self):
        handler = AttachmentHandler()
        handler.MAX_TOTAL_ATTACHMENTS = 2
        handler.add_attachment("L-001", "ATT-001", "a.pdf")
        handler.add_attachment("L-002", "ATT-002", "b.pdf")
        ref = handler.add_attachment("L-003", "ATT-003", "c.pdf")
        assert ref is None

    def test_clear(self):
        handler = AttachmentHandler()
        handler.add_attachment("L-001", "ATT-001", "a.pdf")
        handler.clear()
        assert handler.total_attachments == 0
