from __future__ import annotations

import os
import platform
import subprocess
import tempfile
from typing import Any

from loguru import logger


class PrintEngine:
    def __init__(self, pdf_engine: Any) -> None:
        self._pdf_engine = pdf_engine

    def print_letter(self, letter_data: dict[str, Any], printer_name: str | None = None, copies: int = 1, page_size: str = "A4") -> bool:
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            pdf_path = tmp.name
        try:
            self._pdf_engine.generate_letter_pdf(letter_data, pdf_path, page_size)
            return self._print_pdf(pdf_path, printer_name, copies)
        finally:
            try:
                os.unlink(pdf_path)
            except OSError:
                pass

    def print_existing_pdf(self, pdf_path: str, printer_name: str | None = None, copies: int = 1) -> bool:
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF not found: {pdf_path}")
        return self._print_pdf(pdf_path, printer_name, copies)

    def _print_pdf(self, pdf_path: str, printer_name: str | None = None, copies: int = 1) -> bool:
        system = platform.system()
        try:
            if system == "Windows":
                return self._print_windows(pdf_path, printer_name, copies)
            elif system == "Linux":
                return self._print_linux(pdf_path, printer_name, copies)
            elif system == "Darwin":
                return self._print_macos(pdf_path, printer_name, copies)
            else:
                logger.error(f"Unsupported OS for printing: {system}")
                return False
        except Exception as exc:
            logger.error(f"Print failed: {exc}")
            return False

    def _print_windows(self, pdf_path: str, printer_name: str | None, copies: int) -> bool:
        try:
            import win32api
            import win32print
        except ImportError:
            logger.warning("pywin32 not available, trying PDF fallback")
            return self._print_fallback(pdf_path, copies)

        try:
            current = win32print.GetDefaultPrinter()
            target = printer_name or current
            win32api.ShellExecute(0, "print", pdf_path, f'/d:"{target}"', ".", 0)
            logger.info(f"Sent to printer: {target}, copies: {copies}")
            return True
        except Exception as exc:
            logger.error(f"Windows print failed: {exc}")
            return self._print_fallback(pdf_path, copies)

    def _print_linux(self, pdf_path: str, printer_name: str | None, copies: int) -> bool:
        try:
            cmd = ["lp"]
            if printer_name:
                cmd.extend(["-d", printer_name])
            if copies > 1:
                cmd.extend(["-n", str(copies)])
            cmd.append(pdf_path)
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                logger.info(f"Linux print success: {result.stdout.strip()}")
                return True
            logger.error(f"Linux print failed: {result.stderr}")
            return self._print_fallback(pdf_path, copies)
        except FileNotFoundError:
            logger.warning("CUPS lp command not found")
            return self._print_fallback(pdf_path, copies)
        except subprocess.TimeoutExpired:
            logger.error("Print command timed out")
            return False

    def _print_macos(self, pdf_path: str, printer_name: str | None, copies: int) -> bool:
        return self._print_linux(pdf_path, printer_name, copies)

    def _print_fallback(self, pdf_path: str, copies: int) -> bool:
        system = platform.system()
        try:
            if system == "Windows":
                os.startfile(pdf_path, "print")
            elif system == "Linux":
                subprocess.run(["xdg-open", pdf_path], capture_output=True, timeout=30)
            elif system == "Darwin":
                subprocess.run(["open", pdf_path], capture_output=True, timeout=30)
            logger.info("Fallback print: opened PDF for manual printing")
            return True
        except Exception as exc:
            logger.error(f"Fallback print failed: {exc}")
            return False

    def get_available_printers(self) -> list[dict[str, Any]]:
        system = platform.system()
        printers = []
        try:
            if system == "Windows":
                import win32print
                for p in win32print.EnumPrinters(2):
                    printers.append({"name": p[2], "description": p[3], "is_default": False})
                default = win32print.GetDefaultPrinter()
                for p in printers:
                    if p["name"] == default:
                        p["is_default"] = True
            elif system == "Linux":
                result = subprocess.run(["lpstat", "-e"], capture_output=True, text=True, timeout=30)
                if result.returncode == 0:
                    for line in result.stdout.strip().split("\n"):
                        if line.strip():
                            printers.append({"name": line.strip(), "description": "", "is_default": False})
            elif system == "Darwin":
                result = subprocess.run(["lpstat", "-e"], capture_output=True, text=True, timeout=30)
                if result.returncode == 0:
                    for line in result.stdout.strip().split("\n"):
                        if line.strip():
                            printers.append({"name": line.strip(), "description": "", "is_default": False})
        except Exception as exc:
            logger.warning(f"Could not enumerate printers: {exc}")
        return printers

    def get_default_printer(self) -> str | None:
        system = platform.system()
        try:
            if system == "Windows":
                import win32print
                return win32print.GetDefaultPrinter()
            elif system in ("Linux", "Darwin"):
                result = subprocess.run(["lpstat", "-d"], capture_output=True, text=True, timeout=30)
                if result.returncode == 0 and result.stdout:
                    parts = result.stdout.strip().split(": ")
                    return parts[-1] if len(parts) > 1 else None
        except Exception as exc:
            logger.warning(f"Could not get default printer: {exc}")
        return None
