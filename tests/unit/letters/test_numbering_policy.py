from __future__ import annotations

from app.application.letters.numbering_policy import (
    format_number,
    normalize_sequence,
    parse_number,
    validate_number_format,
    validate_prefix,
    validate_year,
)


class TestValidatePrefix:
    def test_valid_prefixes(self) -> None:
        assert validate_prefix("MOH") is None
        assert validate_prefix("LAB") is None
        assert validate_prefix("ADM") is None

    def test_rejects_lowercase(self) -> None:
        assert validate_prefix("moh") is not None
        assert validate_prefix("Lab") is not None

    def test_rejects_empty(self) -> None:
        assert validate_prefix("") is not None
        assert validate_prefix("   ") is not None

    def test_rejects_too_long(self) -> None:
        assert validate_prefix("TOOLONGPREFIX") is not None

    def test_rejects_special_chars(self) -> None:
        assert validate_prefix("MOH-") is not None
        assert validate_prefix("MOH123") is not None


class TestValidateYear:
    def test_valid_years(self) -> None:
        assert validate_year(2026) is None
        assert validate_year(1900) is None
        assert validate_year(2099) is None

    def test_rejects_out_of_range(self) -> None:
        assert validate_year(1899) is not None
        assert validate_year(2100) is not None


class TestNormalizeSequence:
    def test_fixed_width_padding(self) -> None:
        assert normalize_sequence(1) == "000001"
        assert normalize_sequence(145) == "000145"
        assert normalize_sequence(1522) == "001522"

    def test_rejects_negative(self) -> None:
        import pytest

        with pytest.raises(ValueError):
            normalize_sequence(-1)


class TestFormatNumber:
    def test_known_formats(self) -> None:
        assert format_number("MOH", 2026, 1) == "MOH-2026-000001"
        assert format_number("LAB", 2026, 145) == "LAB-2026-000145"
        assert format_number("ADM", 2026, 1522) == "ADM-2026-001522"

    def test_rejects_invalid_prefix(self) -> None:
        import pytest

        with pytest.raises(ValueError):
            format_number("moh", 2026, 1)

    def test_rejects_invalid_year(self) -> None:
        import pytest

        with pytest.raises(ValueError):
            format_number("MOH", 3000, 1)


class TestValidateNumberFormat:
    def test_valid_formats(self) -> None:
        assert validate_number_format("MOH-2026-000001") is True
        assert validate_number_format("LAB-2026-000145") is True
        assert validate_number_format("ADM-2026-001522") is True

    def test_invalid_formats(self) -> None:
        assert validate_number_format("") is False
        assert validate_number_format("invalid") is False
        assert validate_number_format("moh-2026-000001") is False
        assert validate_number_format("MOH-2026-00001") is False
        assert validate_number_format("MOH-26-000001") is False


class TestParseNumber:
    def test_parse_known_formats(self) -> None:
        assert parse_number("MOH-2026-000001") == ("MOH", 2026, 1)
        assert parse_number("LAB-2026-000145") == ("LAB", 2026, 145)
        assert parse_number("ADM-2026-001522") == ("ADM", 2026, 1522)

    def test_rejects_invalid(self) -> None:
        import pytest

        with pytest.raises(ValueError):
            parse_number("invalid")
