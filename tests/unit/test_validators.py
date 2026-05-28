"""Tests for input validation utilities."""

from pathlib import Path

import pytest

from app.utils.validators import (
    validate_directory_exists,
    validate_email,
    validate_file_exists,
    validate_optional_string,
    validate_required_string,
)


class TestValidateRequiredString:
    def test_valid(self) -> None:
        assert validate_required_string("hello", "field") == "hello"

    def test_strips_whitespace(self) -> None:
        assert validate_required_string("  hello  ", "field") == "hello"

    def test_empty_raises(self) -> None:
        with pytest.raises(ValueError, match="is required"):
            validate_required_string("", "field")

    def test_none_raises(self) -> None:
        with pytest.raises(ValueError, match="required"):
            validate_required_string(None, "field")

    def test_non_string_raises(self) -> None:
        with pytest.raises(ValueError, match="required"):
            validate_required_string(123, "field")

    def test_too_long_raises(self) -> None:
        with pytest.raises(ValueError, match="exceeds maximum"):
            validate_required_string("x" * 600, "field", max_length=500)


class TestValidateOptionalString:
    def test_valid_string(self) -> None:
        assert validate_optional_string("hello", "field") == "hello"

    def test_none_returns_none(self) -> None:
        assert validate_optional_string(None, "field") is None

    def test_too_long_raises(self) -> None:
        with pytest.raises(ValueError, match="exceeds maximum"):
            validate_optional_string("x" * 600, "field", max_length=500)


class TestValidateEmail:
    def test_valid_email(self) -> None:
        assert validate_email("user@example.com") == "user@example.com"

    def test_valid_email_with_plus(self) -> None:
        assert validate_email("user+tag@example.com") == "user+tag@example.com"

    def test_invalid_email_raises(self) -> None:
        with pytest.raises(ValueError, match="Invalid email"):
            validate_email("not-an-email")

    def test_none_returns_none(self) -> None:
        assert validate_email(None) is None


class TestValidateDirectoryExists:
    def test_existing_directory(self, tmp_path: Path) -> None:
        assert validate_directory_exists(tmp_path) == tmp_path

    def test_missing_directory_raises(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            validate_directory_exists(tmp_path / "missing")

    def test_file_raises(self, tmp_path: Path) -> None:
        f = tmp_path / "file.txt"
        f.write_bytes(b"a")
        with pytest.raises(NotADirectoryError):
            validate_directory_exists(f)


class TestValidateFileExists:
    def test_existing_file(self, tmp_path: Path) -> None:
        f = tmp_path / "exists.txt"
        f.write_bytes(b"a")
        assert validate_file_exists(f) == f

    def test_missing_file_raises(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            validate_file_exists(tmp_path / "missing.txt")

    def test_directory_raises(self, tmp_path: Path) -> None:
        with pytest.raises(IsADirectoryError):
            validate_file_exists(tmp_path)
