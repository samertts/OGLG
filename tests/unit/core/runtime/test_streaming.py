from __future__ import annotations

import io

import pytest

from app.core.runtime.streaming import StreamingProcessor


def test_streaming_basic() -> None:
    processor = StreamingProcessor(chunk_size=4)
    data = b"hello world"
    stream = io.BytesIO(data)
    chunks = list(processor.iter_stream(stream))
    assert chunks == [b"hell", b"o wo", b"rld"]


def test_streaming_to_bytes() -> None:
    processor = StreamingProcessor(chunk_size=3)
    data = b"abcdefghij"
    stream = io.BytesIO(data)
    result = processor.to_bytes(stream)
    assert result == data


def test_streaming_process_stream() -> None:
    processor = StreamingProcessor(chunk_size=2, max_chunks=3)
    data = b"0123456789"
    stream = io.BytesIO(data)

    processed: list[bytes] = []

    def collector(chunk: bytes) -> None:
        processed.append(chunk)

    result = processor.process_stream(stream, collector)
    assert result.total_bytes == 6
    assert result.chunk_count == 3
    assert processed == [b"01", b"23", b"45"]


def test_streaming_max_chunks() -> None:
    processor = StreamingProcessor(chunk_size=1, max_chunks=3)
    data = b"abcdef"
    stream = io.BytesIO(data)
    chunks = list(processor.iter_stream(stream))
    assert len(chunks) == 3
    assert b"".join(chunks) == b"abc"


def test_streaming_empty() -> None:
    processor = StreamingProcessor(chunk_size=1024)
    stream = io.BytesIO(b"")
    chunks = list(processor.iter_stream(stream))
    assert chunks == []


def test_streaming_invalid_chunk_size() -> None:
    with pytest.raises(ValueError):
        StreamingProcessor(chunk_size=0)
