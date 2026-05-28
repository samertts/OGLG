from __future__ import annotations

from datetime import datetime
from typing import Any

from loguru import logger


class PdfEngine:
    PAGE_WIDTHS = {"A4": 595.28, "LEGAL": 612.0, "LETTER": 612.0}
    PAGE_HEIGHTS = {"A4": 841.89, "LEGAL": 1008.0, "LETTER": 792.0}
    DEFAULT_MARGINS = {"top": 72, "bottom": 72, "left": 72, "right": 72}

    def __init__(self, font_path: str | None = None) -> None:
        self._font_path = font_path

    def generate_letter_pdf(self, letter_data: dict[str, Any], output_path: str, page_size: str = "A4") -> str:
        try:
            from reportlab.lib.pagesizes import A4, legal, letter
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            from reportlab.pdfgen import canvas
        except ImportError:
            logger.warning("ReportLab not available, using fallback PDF generation")
            return self._generate_fallback_pdf(letter_data, output_path)

        sizes = {"A4": A4, "LEGAL": legal, "LETTER": letter}
        page_size_tuple = sizes.get(page_size, A4)
        pw, ph = page_size_tuple
        margin = 72
        c = canvas.Canvas(output_path, pagesize=page_size_tuple)
        c.setTitle(letter_data.get("subject", "Official Correspondence"))
        c.setAuthor(letter_data.get("sender_name", ""))
        c.setSubject("Government Correspondence")

        if self._font_path:
            try:
                pdfmetrics.registerFont(TTFont("Arabic", self._font_path))
                font_name = "Arabic"
            except Exception:
                font_name = "Helvetica"
        else:
            font_name = "Helvetica"

        y = ph - margin
        line_height = 14

        c.setFont(font_name, 16)
        c.drawString(margin, y, "Official Government Correspondence")
        y -= line_height * 2

        c.setFont(font_name, 8)
        c.drawString(margin, y, f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        y -= line_height

        if letter_data.get("number"):
            c.drawString(margin, y, f"Reference: {letter_data['number']}")
            y -= line_height * 2

        c.setStrokeColorRGB(0, 0, 0)
        c.setLineWidth(0.5)
        c.line(margin, y, pw - margin, y)
        y -= line_height

        c.setFont(font_name, 11)
        fields = [
            ("From:", letter_data.get("sender_name", "")),
            ("Department:", letter_data.get("sender_department", "")),
            ("To:", letter_data.get("recipient_name", "")),
            ("Recipient Dept:", letter_data.get("recipient_department", "")),
            ("Priority:", letter_data.get("priority", "NORMAL")),
            ("Classification:", letter_data.get("classification", "INTERNAL")),
        ]
        for label, value in fields:
            c.drawString(margin, y, f"{label} {value}")
            y -= line_height

        y -= line_height
        c.setStrokeColorRGB(0, 0, 0)
        c.setLineWidth(0.5)
        c.line(margin, y, pw - margin, y)
        y -= line_height

        c.setFont(font_name, 12)
        c.drawString(margin, y, letter_data.get("subject", ""))
        y -= line_height * 2

        c.setFont(font_name, 10)
        body_text = letter_data.get("body", "")
        max_width = pw - 2 * margin
        words = body_text.split()
        line = ""
        for word in words:
            test = f"{line} {word}".strip()
            if c.stringWidth(test, font_name, 10) < max_width:
                line = test
            else:
                c.drawString(margin, y, line)
                y -= line_height
                line = word
                if y < margin + 40:
                    c.showPage()
                    c.setFont(font_name, 10)
                    y = ph - margin
        if line:
            c.drawString(margin, y, line)
            y -= line_height

        y -= line_height * 2
        c.setFont(font_name, 8)
        c.drawString(margin, y, "--- Document metadata ---")
        y -= line_height
        c.drawString(margin, y, f"Generated: {datetime.now().isoformat()}")
        y -= line_height
        c.drawString(margin, y, f"Language: {letter_data.get('language', 'AR')}")
        y -= line_height
        c.drawString(margin, y, "Page 1 of 1")

        c.save()
        logger.info(f"PDF generated: {output_path}")
        return output_path

    def generate_batch(self, letters: list[dict[str, Any]], output_dir: str, page_size: str = "A4") -> list[str]:
        import os

        paths = []
        for letter in letters:
            safe_name = f"{letter.get('id', 'letter')}_{letter.get('number', 'unnumbered')}.pdf".replace("/", "_")
            output_path = os.path.join(output_dir, safe_name)
            self.generate_letter_pdf(letter, output_path, page_size)
            paths.append(output_path)
        return paths

    def _generate_fallback_pdf(self, letter_data: dict[str, Any], output_path: str) -> str:
        with open(output_path, "wb") as f:
            f.write(b"%PDF-1.4\n")
            f.write(b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n")
            f.write(b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n")
            f.write(b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n")
            subject = letter_data.get("subject", "Letter").encode("latin-1", "replace")
            body = letter_data.get("body", "")[:200].encode("latin-1", "replace")
            content = f"""
BT
/F1 12 Tf
50 800 Td
({subject.decode('latin-1', 'replace')}) Tj
ET
BT
/F1 10 Tf
50 770 Td
({body.decode('latin-1', 'replace')}) Tj
ET
""".encode()
            f.write(b"4 0 obj\n<< /Length %d >>\nstream\n" % len(content))
            f.write(content)
            f.write(b"\nendstream\nendobj\n")
            f.write(b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n")
            f.write(b"xref\n0 6\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000266 00000 n \n0000000378 00000 n \n")
            f.write(b"trailer\n<< /Size 6 /Root 1 0 R >>\n")
            f.write(b"startxref\n436\n%%EOF\n")
        logger.info(f"Fallback PDF generated: {output_path}")
        return output_path
