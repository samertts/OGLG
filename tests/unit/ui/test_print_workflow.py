from __future__ import annotations

from app.ui.core.pdf_generator import PdfGenerationState, PdfJob, PdfJobManager
from app.ui.core.print_models import (
    DocumentSection,
    DocumentTemplate,
    FooterMetadata,
    PageLayout,
    PageNumbering,
    PageOrientation,
    PrintDocument,
)


class TestPageLayout:
    def test_a4_defaults(self):
        layout = PageLayout()
        assert layout.width_mm == 210.0
        assert layout.height_mm == 297.0
        assert layout.orientation == PageOrientation.PORTRAIT

    def test_content_width(self):
        layout = PageLayout(margin_left_mm=25, margin_right_mm=25)
        assert layout.content_width_mm == 160.0

    def test_content_height(self):
        layout = PageLayout(margin_top_mm=25, margin_bottom_mm=25)
        assert layout.content_height_mm == 247.0

    def test_a4_landscape(self):
        layout = PageLayout()
        layout.as_a4_landscape()
        assert layout.width_mm == 297.0
        assert layout.height_mm == 210.0
        assert layout.orientation == PageOrientation.LANDSCAPE


class TestFooterMetadata:
    def test_render_lines_with_all(self):
        footer = FooterMetadata(
            organization="Ministry of Health",
            document_id="DOC-001",
            page_number=1, total_pages=5,
            printed_at="2026-05-31",
            classification="confidential",
        )
        lines = footer.render_lines()
        assert "Ministry of Health" in lines
        assert "DOC-001" in lines[1]
        assert any("Page 1 of 5" in ln for ln in lines)
        assert "[CONFIDENTIAL]" in lines

    def test_render_lines_no_classification(self):
        footer = FooterMetadata(organization="Ministry")
        lines = footer.render_lines()
        assert "[CONFIDENTIAL]" not in lines

    def test_empty_footer(self):
        footer = FooterMetadata()
        lines = footer.render_lines()
        assert lines == []


class TestPageNumbering:
    def test_default_format(self):
        pn = PageNumbering()
        result = pn.format(1, 10)
        assert result == "Page 1 of 10"

    def test_start_page_offset(self):
        pn = PageNumbering(start_page=5)
        result = pn.format(1, 10)
        assert result == "Page 5 of 10"

    def test_custom_format(self):
        pn = PageNumbering(format_str="{page}/{total}")
        result = pn.format(3, 10)
        assert result == "3/10"


class TestDocumentTemplate:
    def test_default_template(self):
        t = DocumentTemplate()
        assert t.template_id == "default"
        assert t.rtl
        assert t.layout.orientation == PageOrientation.PORTRAIT

    def test_custom_template(self):
        t = DocumentTemplate(
            template_id="official",
            name="Official Letter",
            font_size_body=12.0,
        )
        assert t.name == "Official Letter"


class TestPrintDocument:
    def test_create_document(self):
        doc = PrintDocument(document_id="DOC-001", title="Annual Report")
        assert doc.document_id == "DOC-001"
        assert doc.total_sections == 0

    def test_add_section(self):
        doc = PrintDocument(document_id="D-001")
        doc.add_section("Introduction", "Hello world")
        assert doc.total_sections == 1
        assert doc.sections[0].title == "Introduction"

    def test_estimated_pages(self):
        doc = PrintDocument(document_id="D-001")
        doc.add_section("Long", "A" * 9000)
        assert doc.estimated_pages >= 3


class TestPdfJob:
    def test_initial_state(self):
        job = PdfJob(job_id="J-001", document_id="D-001")
        assert job.state == PdfGenerationState.IDLE
        assert not job.is_terminal

    def test_terminal_state(self):
        job = PdfJob(job_id="J-001", document_id="D-001")
        job.state = PdfGenerationState.COMPLETED
        assert job.is_terminal
        assert job.is_success

    def test_failed_state(self):
        job = PdfJob(job_id="J-001", document_id="D-001")
        job.state = PdfGenerationState.FAILED
        assert job.is_terminal
        assert not job.is_success


class TestPdfJobManager:
    def test_create_job(self):
        mgr = PdfJobManager()
        job = mgr.create_job("J-001", "D-001")
        assert job is not None
        assert mgr.job_count == 1

    def test_create_job_at_capacity(self):
        mgr = PdfJobManager()
        mgr.MAX_JOBS = 2
        mgr.create_job("J-001", "D-001")
        mgr.create_job("J-002", "D-002")
        job = mgr.create_job("J-003", "D-003")
        assert job is None

    def test_get_job(self):
        mgr = PdfJobManager()
        mgr.create_job("J-001", "D-001")
        job = mgr.get_job("J-001")
        assert job is not None

    def test_complete_job(self):
        mgr = PdfJobManager()
        mgr.create_job("J-001", "D-001")
        assert mgr.complete_job("J-001", 3, 1024)
        job = mgr.get_job("J-001")
        assert job.state == PdfGenerationState.COMPLETED
        assert job.page_count == 3

    def test_complete_job_exceeds_size_limit(self):
        mgr = PdfJobManager()
        mgr.create_job("J-001", "D-001")
        mgr.MAX_SIZE_BYTES = 100
        mgr.complete_job("J-001", 1, 200)
        job = mgr.get_job("J-001")
        assert job.state == PdfGenerationState.FAILED

    def test_fail_job(self):
        mgr = PdfJobManager()
        mgr.create_job("J-001", "D-001")
        assert mgr.fail_job("J-001", "Error")
        job = mgr.get_job("J-001")
        assert job.error_message == "Error"

    def test_cancel_job(self):
        mgr = PdfJobManager()
        mgr.create_job("J-001", "D-001")
        assert mgr.cancel_job("J-001")
        job = mgr.get_job("J-001")
        assert job.state == PdfGenerationState.CANCELLED

    def test_cancel_terminal_job_fails(self):
        mgr = PdfJobManager()
        mgr.create_job("J-001", "D-001")
        mgr.complete_job("J-001", 1, 100)
        assert not mgr.cancel_job("J-001")

    def test_clean_old_jobs(self):
        mgr = PdfJobManager()
        mgr.create_job("J-001", "D-001")
        mgr.complete_job("J-001", 1, 100)
        cleaned = mgr.clean_old_jobs(max_age_seconds=0)
        assert cleaned == 1
        assert mgr.job_count == 0

    def test_job_ids(self):
        mgr = PdfJobManager()
        mgr.create_job("J-001", "D-001")
        mgr.create_job("J-002", "D-002")
        assert mgr.job_ids == ["J-001", "J-002"]

    def test_clear(self):
        mgr = PdfJobManager()
        mgr.create_job("J-001", "D-001")
        mgr.clear()
        assert mgr.job_count == 0
