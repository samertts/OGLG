"""Tests for domain value objects."""

from datetime import date, datetime

import uuid

import pytest

from app.core.value_objects.date_range import DateRange
from app.core.value_objects.document_id import DocumentId
from app.core.value_objects.letter_number import LetterNumber
from app.core.value_objects.sha256_hash import SHA256Hash


class TestLetterNumber:
    def test_create_valid(self) -> None:
        ln = LetterNumber.create("MOH", 2024, 1)
        assert ln.prefix == "MOH"
        assert ln.year == 2024
        assert ln.sequence == 1

    def test_parse_valid_full_format(self) -> None:
        ln = LetterNumber.parse("MOH-2024-0001")
        assert ln.prefix == "MOH"
        assert ln.year == 2024
        assert ln.sequence == 1

    def test_parse_valid_large_sequence(self) -> None:
        ln = LetterNumber.parse("FIN-2024-9999")
        assert ln.sequence == 9999

    def test_format(self) -> None:
        ln = LetterNumber.create("MOH", 2024, 1)
        assert ln.format() == "MOH-2024-0001"

    def test_format_large_sequence(self) -> None:
        ln = LetterNumber.create("FIN", 2024, 9999)
        assert ln.format() == "FIN-2024-9999"

    def test_parse_invalid_format(self) -> None:
        with pytest.raises(ValueError):
            LetterNumber.parse("invalid")

    def test_parse_empty(self) -> None:
        with pytest.raises(ValueError):
            LetterNumber.parse("")

    def test_create_invalid_prefix_length(self) -> None:
        with pytest.raises(ValueError):
            LetterNumber.create("X", 2024, 1)

    def test_create_invalid_year(self) -> None:
        with pytest.raises(ValueError):
            LetterNumber.create("MOH", 1999, 1)

    def test_equality(self) -> None:
        a = LetterNumber.create("MOH", 2024, 1)
        b = LetterNumber.create("MOH", 2024, 1)
        c = LetterNumber.create("MOH", 2024, 2)
        assert a == b
        assert a != c

    def test_string_representation(self) -> None:
        ln = LetterNumber.create("MOH", 2024, 1)
        assert str(ln) == "MOH-2024-0001"


class TestSHA256Hash:
    def test_create_valid_hash(self) -> None:
        h = SHA256Hash("a" * 64)
        assert h.value == "a" * 64

    def test_compute_from_data(self) -> None:
        h = SHA256Hash.compute(b"test data")
        expected = "916f0027a575074ce72a331777c3478d6513f786a591bd892da1a577bf2335f9"
        assert h.value == expected

    def test_compute_from_string(self) -> None:
        h = SHA256Hash.compute_from_string("hello world")
        expected = "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"
        assert h.value == expected

    def test_invalid_hex_length(self) -> None:
        with pytest.raises(ValueError):
            SHA256Hash("abc")

    def test_invalid_hex_characters(self) -> None:
        with pytest.raises(ValueError):
            SHA256Hash("z" + "0" * 63)

    def test_empty_data(self) -> None:
        h = SHA256Hash.compute(b"")
        assert h.value == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

    def test_matches_data(self) -> None:
        h = SHA256Hash.compute(b"test data")
        assert h.matches(b"test data")
        assert not h.matches(b"different data")

    def test_equality(self) -> None:
        a = SHA256Hash("a" * 64)
        b = SHA256Hash("a" * 64)
        c = SHA256Hash("b" * 64)
        assert a == b
        assert a != c

    def test_string_representation(self) -> None:
        h = SHA256Hash("a" * 64)
        assert str(h) == "a" * 64


class TestDocumentId:
    def test_new_generates_uuid(self) -> None:
        doc_id = DocumentId.new()
        assert isinstance(doc_id.value, uuid.UUID)

    def test_from_string_valid(self) -> None:
        doc_id = DocumentId.from_string("550e8400-e29b-41d4-a716-446655440000")
        assert str(doc_id.value) == "550e8400-e29b-41d4-a716-446655440000"

    def test_from_string_invalid(self) -> None:
        with pytest.raises(ValueError):
            DocumentId.from_string("not-a-uuid")

    def test_equality(self) -> None:
        a = DocumentId.from_string("550e8400-e29b-41d4-a716-446655440000")
        b = DocumentId.from_string("550e8400-e29b-41d4-a716-446655440000")
        c = DocumentId.from_string("660e8400-e29b-41d4-a716-446655440000")
        assert a == b
        assert a != c

    def test_string_representation(self) -> None:
        uid = "550e8400-e29b-41d4-a716-446655440000"
        doc_id = DocumentId.from_string(uid)
        assert str(doc_id) == uid


class TestDateRange:
    def test_valid_range(self) -> None:
        dr = DateRange(date(2024, 1, 1), date(2024, 12, 31))
        assert dr.start_date == date(2024, 1, 1)
        assert dr.end_date == date(2024, 12, 31)

    def test_contains(self) -> None:
        dr = DateRange(date(2024, 1, 1), date(2024, 12, 31))
        assert dr.contains(date(2024, 6, 15))
        assert dr.contains(date(2024, 1, 1))
        assert dr.contains(date(2024, 12, 31))
        assert not dr.contains(date(2023, 12, 31))
        assert not dr.contains(date(2025, 1, 1))

    def test_is_empty(self) -> None:
        assert DateRange().is_empty()
        assert not DateRange(date(2024, 1, 1), None).is_empty()
        assert not DateRange(None, date(2024, 12, 31)).is_empty()

    def test_from_datetime(self) -> None:
        start = datetime(2024, 1, 1, 10, 0)
        end = datetime(2024, 12, 31, 18, 0)
        dr = DateRange.from_datetime(start, end)
        assert dr.start_date == date(2024, 1, 1)
        assert dr.end_date == date(2024, 12, 31)

    def test_from_strings(self) -> None:
        dr = DateRange.from_strings("2024-01-01", "2024-12-31")
        assert dr.start_date == date(2024, 1, 1)
        assert dr.end_date == date(2024, 12, 31)

    def test_from_strings_none(self) -> None:
        dr = DateRange.from_strings(None, None)
        assert dr.is_empty()
