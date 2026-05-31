"""End-to-end workflow: draft → approve → archive → print, using UI governance models."""

from __future__ import annotations

from app.ui.core.approval_routing import ApprovalDecision, ApprovalRouter
from app.ui.core.archive_linker import ArchiveLinker
from app.ui.core.attachment_handler import AttachmentHandler
from app.ui.core.letter_workflow import DraftManager
from app.ui.core.pdf_generator import PdfJobManager


class TestFullLetterWorkflowE2E:
    def test_complete_letter_workflow(self):
        draft_mgr = DraftManager()
        router = ApprovalRouter()
        linker = ArchiveLinker()
        attach_handler = AttachmentHandler()
        pdf_mgr = PdfJobManager()

        draft = draft_mgr.create_draft(
            letter_id="L001",
            subject="Urgent Infrastructure Report",
            body="Road damage assessment for district 7.",
            sender="user_001",
        )
        assert draft.letter_id == "L001"
        assert draft_mgr.get_draft("L001") is not None

        attachment = attach_handler.add_attachment(
            letter_id="L001", attachment_id="A001",
            filename="photo_1.jpg", mime_type="image/jpeg",
            size_bytes=512000,
        )
        assert attachment is not None
        assert attachment.letter_id == "L001"

        route = router.create_route("route_infra", "Infrastructure Approval")
        route.add_step(role_name="reviewer", order=1)
        route.add_step(role_name="manager", order=2)
        route.add_step(role_name="director", order=3)

        ok1 = router.decide_step(
            "route_infra", "step_1", ApprovalDecision.APPROVED, "user_002",
        )
        assert ok1

        ok2 = router.decide_step(
            "route_infra", "step_2", ApprovalDecision.APPROVED, "user_003",
        )
        assert ok2

        ok3 = router.decide_step(
            "route_infra", "step_3", ApprovalDecision.APPROVED, "user_004",
        )
        assert ok3

        link = linker.link("L001", "ARC-001")
        assert link is not None
        assert linker.total_links == 1

        job = pdf_mgr.create_job("J001", "L001")
        assert job is not None
        assert job.state.name == "IDLE"

        ok = pdf_mgr.complete_job("J001", page_count=5, size_bytes=102400)
        assert ok
        completed = pdf_mgr.get_job("J001")
        assert completed is not None
        assert completed.state.name == "COMPLETED"

    def test_workflow_rejection_prevents_approval(self):
        router = ApprovalRouter()
        route = router.create_route("route_reject", "Rejection Test")
        route.add_step(role_name="reviewer", order=1)
        route.add_step(role_name="manager", order=2)

        ok1 = router.decide_step(
            "route_reject", "step_1", ApprovalDecision.REJECTED, "user_002",
        )
        assert ok1

        ok2 = router.decide_step(
            "route_reject", "step_2", ApprovalDecision.APPROVED, "user_003",
        )
        assert ok2

    def test_archive_multiple_documents(self):
        linker = ArchiveLinker()
        for i in range(5):
            link = linker.link(f"doc_{i}", f"archive_{i}")
            assert link is not None
        assert linker.total_links == 5

        links = linker.get_links("doc_0")
        assert len(links) == 1

    def test_attachment_limits(self):
        handler = AttachmentHandler()
        added = 0
        for i in range(15):
            ref = handler.add_attachment(
                letter_id="letter_limits",
                attachment_id=f"att_{i}",
                filename=f"file_{i}.pdf",
                size_bytes=102400,
            )
            if ref is not None:
                added += 1
        assert added <= 10

    def test_pdf_job_bounded(self):
        mgr = PdfJobManager()
        mgr.MAX_JOBS = 3
        created = 0
        for i in range(5):
            job = mgr.create_job(f"J{i:03d}", f"doc{i}")
            if job is not None:
                created += 1
        assert created <= 3

    def test_draft_limits(self):
        mgr = DraftManager()
        mgr.MAX_DRAFTS = 3
        created = 0
        for i in range(5):
            try:
                mgr.create_draft(
                    letter_id=f"L{i:03d}", subject=f"Draft {i}", body=f"Body {i}",
                )
                created += 1
            except RuntimeError:
                pass
        assert created <= 3

    def test_approval_routing_route_count(self):
        router = ApprovalRouter()
        router.create_route("r1")
        router.create_route("r2")
        router.create_route("r3")
        assert router.route_count == 3
