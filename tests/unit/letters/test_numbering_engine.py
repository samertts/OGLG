from __future__ import annotations

from datetime import datetime

import pytest

from app.application.letters.numbering_engine import NumberingEngine


class MockSequenceProvider:
    def __init__(self) -> None:
        self._counter: dict[tuple[str, int], int] = {}

    def next_sequence(self, department_code: str, year: int, count: int = 1) -> int:
        key = (department_code, year)
        current = self._counter.get(key, 0)
        self._counter[key] = current + count
        return current + 1


class TestNumberingEngine:
    def test_generate_simple(self) -> None:
        provider = MockSequenceProvider()
        engine = NumberingEngine(provider)
        number = engine.generate("MOH", 2026)
        assert number == "MOH-2026-000001"

    def test_generate_default_year(self) -> None:
        provider = MockSequenceProvider()
        engine = NumberingEngine(provider)
        current_year = datetime.now().year
        number = engine.generate("LAB")
        assert number.startswith(f"LAB-{current_year}-")

    def test_generate_department_aware(self) -> None:
        provider = MockSequenceProvider()
        engine = NumberingEngine(provider)
        moh_num = engine.generate("MOH", 2026)
        lab_num = engine.generate("LAB", 2026)
        assert moh_num == "MOH-2026-000001"
        assert lab_num == "LAB-2026-000001"

    def test_generate_incrementing(self) -> None:
        provider = MockSequenceProvider()
        engine = NumberingEngine(provider)
        n1 = engine.generate("MOH", 2026)
        n2 = engine.generate("MOH", 2026)
        n3 = engine.generate("MOH", 2026)
        assert n1 == "MOH-2026-000001"
        assert n2 == "MOH-2026-000002"
        assert n3 == "MOH-2026-000003"

    def test_generate_year_separate(self) -> None:
        provider = MockSequenceProvider()
        engine = NumberingEngine(provider)
        n1 = engine.generate("MOH", 2026)
        n2 = engine.generate("MOH", 2027)
        assert n1 == "MOH-2026-000001"
        assert n2 == "MOH-2027-000001"

    def test_generate_batch(self) -> None:
        provider = MockSequenceProvider()
        engine = NumberingEngine(provider)
        numbers = engine.generate_batch("MOH", 3, 2026)
        assert len(numbers) == 3
        assert numbers[0] == "MOH-2026-000001"
        assert numbers[1] == "MOH-2026-000002"
        assert numbers[2] == "MOH-2026-000003"

    def test_generate_batch_invalid_count(self) -> None:
        provider = MockSequenceProvider()
        engine = NumberingEngine(provider)
        with pytest.raises(ValueError):
            engine.generate_batch("MOH", 0, 2026)

    def test_generate_batch_exceeds_limit(self) -> None:
        provider = MockSequenceProvider()
        engine = NumberingEngine(provider)
        with pytest.raises(ValueError):
            engine.generate_batch("MOH", 1001, 2026)

    def test_empty_department_code(self) -> None:
        provider = MockSequenceProvider()
        engine = NumberingEngine(provider)
        with pytest.raises(ValueError):
            engine.generate("", 2026)

    def test_parse_number(self) -> None:
        provider = MockSequenceProvider()
        engine = NumberingEngine(provider)
        prefix, year, seq = engine.parse_number("MOH-2026-000001")
        assert prefix == "MOH"
        assert year == 2026
        assert seq == 1

    def test_parse_number_invalid(self) -> None:
        provider = MockSequenceProvider()
        engine = NumberingEngine(provider)
        with pytest.raises(ValueError):
            engine.parse_number("invalid")

    def test_validate_number(self) -> None:
        provider = MockSequenceProvider()
        engine = NumberingEngine(provider)
        assert engine.validate_number("MOH-2026-000001")
        assert engine.validate_number("LAB-2026-000145")
        assert not engine.validate_number("invalid")
        assert not engine.validate_number("")

    def test_concurrent_safety(self) -> None:
        import threading

        provider = MockSequenceProvider()
        engine = NumberingEngine(provider)
        results: list[str] = []
        lock = threading.Lock()

        def generate() -> None:
            num = engine.generate("MOH", 2026)
            with lock:
                results.append(num)

        threads = [threading.Thread(target=generate) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(results) == 10
        unique = set(results)
        assert len(unique) == 10


class TestNumberFormat:
    def test_example_moh(self) -> None:
        provider = MockSequenceProvider()
        engine = NumberingEngine(provider)
        num = engine.generate("MOH", 2026)
        assert num == "MOH-2026-000001"

    def test_example_lab(self) -> None:
        provider = MockSequenceProvider()
        engine = NumberingEngine(provider)
        engine.generate("MOH", 2026)
        num = engine.generate("LAB", 2026)
        assert num == "LAB-2026-000001"

    def test_long_code(self) -> None:
        provider = MockSequenceProvider()
        engine = NumberingEngine(provider)
        with pytest.raises(ValueError):
            engine.generate("TOOLONGCODE", 2026)
