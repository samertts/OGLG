from __future__ import annotations

from datetime import datetime

from app.application.letters.numbering_sequence import NumberingSequence


class TestNumberingSequence:
    def test_create_sequence(self) -> None:
        seq = NumberingSequence(prefix="MOH", year=2026, last_sequence=0)
        assert seq.prefix == "MOH"
        assert seq.year == 2026
        assert seq.last_sequence == 0

    def test_next_value(self) -> None:
        seq = NumberingSequence(prefix="MOH", year=2026, last_sequence=5)
        assert seq.next_value() == 6

    def test_next_value_at_zero(self) -> None:
        seq = NumberingSequence(prefix="MOH", year=2026, last_sequence=0)
        assert seq.next_value() == 1

    def test_with_increment(self) -> None:
        seq = NumberingSequence(prefix="MOH", year=2026, last_sequence=0)
        next_seq = seq.with_increment(1)
        assert next_seq.last_sequence == 1
        assert next_seq.prefix == "MOH"
        assert next_seq.year == 2026

    def test_with_increment_batch(self) -> None:
        seq = NumberingSequence(prefix="MOH", year=2026, last_sequence=0)
        next_seq = seq.with_increment(5)
        assert next_seq.last_sequence == 5

    def test_immutability(self) -> None:
        seq = NumberingSequence(prefix="MOH", year=2026, last_sequence=0)
        next_seq = seq.with_increment(1)
        assert seq.last_sequence == 0
        assert next_seq.last_sequence == 1

    def test_to_dict(self) -> None:
        seq = NumberingSequence(prefix="MOH", year=2026, last_sequence=42)
        d = seq.to_dict()
        assert d["prefix"] == "MOH"
        assert d["year"] == 2026
        assert d["last_sequence"] == 42
        assert "created_at" in d

    def test_effective_year(self) -> None:
        seq = NumberingSequence(prefix="MOH", year=2026, last_sequence=0)
        assert seq.effective_year == 2026

    def test_updated_at_none_by_default(self) -> None:
        seq = NumberingSequence(prefix="MOH", year=2026, last_sequence=0)
        assert seq.updated_at is None

    def test_with_increment_sets_updated_at(self) -> None:
        seq = NumberingSequence(prefix="MOH", year=2026, last_sequence=0)
        next_seq = seq.with_increment(1)
        assert next_seq.updated_at is not None

    def test_created_at_is_datetime(self) -> None:
        seq = NumberingSequence(prefix="MOH", year=2026, last_sequence=0)
        assert isinstance(seq.created_at, datetime)
