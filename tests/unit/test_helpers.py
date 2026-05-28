"""Tests for helper utility functions."""

import json
from datetime import datetime
from pathlib import Path

import pytest

from app.utils.helpers import (
    format_timestamp,
    load_json,
    parse_timestamp,
    sanitize_filename,
    save_json,
)


class TestLoadJson:
    def test_load_json(self, tmp_path: Path) -> None:
        f = tmp_path / "data.json"
        f.write_text('{"key": "value"}', encoding="utf-8")
        assert load_json(f) == {"key": "value"}

    def test_load_json_not_found(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            load_json(tmp_path / "nope.json")


class TestSaveJson:
    def test_save_json(self, tmp_path: Path) -> None:
        f = tmp_path / "output.json"
        save_json(f, {"a": 1, "b": 2})
        assert f.exists()
        data = json.loads(f.read_bytes())
        assert data == {"a": 1, "b": 2}

    def test_save_json_atomic(self, tmp_path: Path) -> None:
        f = tmp_path / "atomic.json"
        save_json(f, {"key": "value"}, atomic=True)
        assert f.exists()
        # No .tmp leftovers
        assert list(tmp_path.glob("*.tmp")) == []


class TestFormatTimestamp:
    def test_format_timestamp(self) -> None:
        dt = datetime(2024, 6, 15, 10, 30, 0)
        assert format_timestamp(dt) == "2024-06-15T10:30:00"

    def test_format_timestamp_none(self) -> None:
        assert format_timestamp(None) is None


class TestParseTimestamp:
    def test_parse_timestamp(self) -> None:
        dt = parse_timestamp("2024-06-15T10:30:00")
        assert dt is not None
        assert dt.year == 2024
        assert dt.month == 6

    def test_parse_timestamp_none(self) -> None:
        assert parse_timestamp(None) is None

    def test_parse_timestamp_empty(self) -> None:
        assert parse_timestamp("") is None


class TestSanitizeFilename:
    def test_sanitize_removes_bad_chars(self) -> None:
        result = sanitize_filename("file:name?.txt")
        assert ":" not in result
        assert "?" not in result

    def test_sanitize_keeps_good(self) -> None:
        result = sanitize_filename("hello_world.txt")
        assert result == "hello_world.txt"

    def test_sanitize_truncates_long(self) -> None:
        long_name = "x" * 300 + ".txt"
        result = sanitize_filename(long_name)
        assert len(result) <= 200

    def test_sanitize_empty_fallback(self) -> None:
        result = sanitize_filename("")
        assert result == "unnamed"

    def test_sanitize_strips_leading_dots(self) -> None:
        result = sanitize_filename("..hidden.txt")
        assert not result.startswith(".")

    def test_sanitize_strips_trailing_dots(self) -> None:
        result = sanitize_filename("file...")
        assert not result.endswith(".")
