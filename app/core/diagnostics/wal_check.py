from __future__ import annotations

import os
import struct
from pathlib import Path
from typing import Any


class WalConsistencyChecker:
    """WAL integrity validation for SQLite WAL files.

    Reads WAL headers and checks basic structural integrity.
    """

    WAL_HEADER_MAGIC = b"SQLite format 3\x00"
    WAL_HEADER_SIZE = 36
    WAL_FRAME_HEADER_SIZE = 24

    def __init__(self, wal_path: str | Path) -> None:
        self._path = Path(wal_path)

    @property
    def path(self) -> Path:
        return self._path

    def exists(self) -> bool:
        return self._path.exists()

    def check(self) -> dict[str, Any]:
        if not self._path.exists():
            return {
                "valid": True,
                "exists": False,
                "message": "WAL file does not exist (not in WAL mode or empty)",
            }
        try:
            with open(self._path, "rb") as f:
                header = f.read(self.WAL_HEADER_SIZE)
                if len(header) < self.WAL_HEADER_SIZE:
                    return {
                        "valid": False,
                        "exists": True,
                        "message": "WAL header truncated",
                    }
                magic = header[:16]
                if magic != self.WAL_HEADER_MAGIC:
                    return {
                        "valid": False,
                        "exists": True,
                        "message": f"Invalid WAL magic: {magic!r}",
                    }
                version = struct.unpack(">I", header[16:20])[0]
                page_size = struct.unpack(">I", header[20:24])[0]
                checkpoint_seq = struct.unpack(">I", header[24:28])[0]
                salt_1 = struct.unpack(">I", header[28:32])[0]
                salt_2 = struct.unpack(">I", header[32:36])[0]
                f.seek(0, os.SEEK_END)
                file_size = f.tell()
                frame_size = page_size + self.WAL_FRAME_HEADER_SIZE
                computed_frames = 0
                if frame_size > 0 and file_size > self.WAL_HEADER_SIZE:
                    computed_frames = (
                        file_size - self.WAL_HEADER_SIZE
                    ) // frame_size
                return {
                    "valid": True,
                    "exists": True,
                    "version": version,
                    "page_size": page_size,
                    "checkpoint_sequence": checkpoint_seq,
                    "salt_1": salt_1,
                    "salt_2": salt_2,
                    "file_size": file_size,
                    "frame_size": frame_size,
                    "computed_frames": computed_frames,
                    "message": "WAL structure valid",
                }
        except OSError as exc:
            return {
                "valid": False,
                "exists": True,
                "message": f"WAL read error: {exc}",
            }
