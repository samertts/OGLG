from __future__ import annotations

import io
from collections.abc import AsyncIterator, Iterator
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

T = TypeVar("T")
ChunkT = TypeVar("ChunkT")


@dataclass
class StreamingResult(Generic[T]):
    data: T
    chunk_count: int
    total_bytes: int


class StreamingProcessor(Generic[ChunkT, T]):
    """Memory-safe streaming file processing foundation."""

    def __init__(
        self,
        chunk_size: int = 65536,
        max_chunks: int = 0,
    ) -> None:
        if chunk_size < 1:
            raise ValueError("chunk_size must be >= 1")
        self._chunk_size = chunk_size
        self._max_chunks = max_chunks

    @property
    def chunk_size(self) -> int:
        return self._chunk_size

    def iter_stream(
        self,
        stream: io.IOBase,
    ) -> Iterator[bytes]:
        chunks = 0
        while True:
            if self._max_chunks > 0 and chunks >= self._max_chunks:
                break
            chunk = stream.read(self._chunk_size)
            if not chunk:
                break
            chunks += 1
            yield chunk

    async def aiter_stream(
        self,
        stream: io.IOBase,
    ) -> AsyncIterator[bytes]:
        for chunk in self.iter_stream(stream):
            yield chunk

    def process_stream(
        self,
        stream: io.IOBase,
        processor: Any,
    ) -> StreamingResult[Any]:
        chunk_count = 0
        total_bytes = 0
        for chunk in self.iter_stream(stream):
            chunk_count += 1
            total_bytes += len(chunk)
            if callable(processor):
                processor(chunk)
        return StreamingResult(
            data=total_bytes,
            chunk_count=chunk_count,
            total_bytes=total_bytes,
        )

    def to_bytes(
        self,
        stream: io.IOBase,
    ) -> bytes:
        result = bytearray()
        for chunk in self.iter_stream(stream):
            result.extend(chunk)
        return bytes(result)
