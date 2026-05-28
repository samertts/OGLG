from __future__ import annotations

import hashlib
import os
import shutil
import tempfile
from pathlib import Path
from typing import BinaryIO


def atomic_write(target_path: Path, content: bytes) -> Path:
    """Write file atomically to prevent partial writes on crash.

    Writes to a temporary file in the same directory, then renames
    atomically. On Windows, os.replace() is used for atomic rename.

    Args:
        target_path: Destination file path.
        content: File content as bytes.

    Returns:
        The target path after successful write.
    """
    target_path = target_path.resolve()
    target_path.parent.mkdir(parents=True, exist_ok=True)

    tmp_path = target_path.with_suffix(f"{target_path.suffix}.tmp")
    tmp_path.write_bytes(content)
    tmp_path.replace(target_path)
    return target_path


def atomic_write_stream(target_path: Path, stream: BinaryIO) -> Path:
    """Write file atomically from a binary stream.

    Args:
        target_path: Destination file path.
        stream: Binary stream to read from.

    Returns:
        The target path after successful write.
    """
    target_path = target_path.resolve()
    target_path.parent.mkdir(parents=True, exist_ok=True)

    tmp_path = target_path.with_suffix(f"{target_path.suffix}.tmp")
    with open(tmp_path, "wb") as f:
        shutil.copyfileobj(stream, f)
    tmp_path.replace(target_path)
    return target_path


def atomic_move(source: Path, target: Path) -> Path:
    """Move a file atomically between directories.

    Args:
        source: Source file path.
        target: Destination file path.

    Returns:
        The target path after successful move.
    """
    target = target.resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    source.replace(target)
    return target


def compute_file_hash(path: Path) -> str:
    """Compute SHA-256 hash of a file.

    Args:
        path: Path to the file.

    Returns:
        Hex-encoded SHA-256 hash string.
    """
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def compute_data_hash(data: bytes) -> str:
    """Compute SHA-256 hash of byte data.

    Args:
        data: Byte data to hash.

    Returns:
        Hex-encoded SHA-256 hash string.
    """
    return hashlib.sha256(data).hexdigest()


def ensure_directory(path: Path) -> Path:
    """Ensure a directory exists, creating it if necessary.

    Args:
        path: Directory path to ensure.

    Returns:
        The path after ensuring it exists.
    """
    path.mkdir(parents=True, exist_ok=True)
    return path


def safe_remove(path: Path) -> bool:
    """Safely remove a file, logging but not raising on failure.

    Args:
        path: Path to the file to remove.

    Returns:
        True if removed, False if not found or error.
    """
    try:
        if path.exists():
            path.unlink()
            return True
        return False
    except OSError:
        return False


def cleanup_temp_files(temp_dir: Path, max_age_hours: int = 24) -> int:
    """Clean up temporary .tmp files in a directory.

    Args:
        temp_dir: Directory to scan for temp files.
        max_age_hours: Max age in hours before deletion.

    Returns:
        Number of files cleaned up.
    """
    import time

    if not temp_dir.exists():
        return 0

    now = time.time()
    max_age_seconds = max_age_hours * 3600
    cleaned = 0

    for tmp_file in temp_dir.glob("*.tmp"):
        try:
            age = now - tmp_file.stat().st_mtime
            if age > max_age_seconds:
                tmp_file.unlink()
                cleaned += 1
        except OSError:
            continue

    return cleaned


def create_temp_file(suffix: str = ".tmp") -> tuple[Path, str]:
    """Create a temporary file and return its path and name.

    Returns:
        Tuple of (Path, filename).
    """
    fd, path = tempfile.mkstemp(suffix=suffix)
    os.close(fd)
    return Path(path), Path(path).name


def get_disk_usage(path: Path) -> tuple[int, int, int]:
    """Get disk usage statistics for a path.

    Args:
        path: Path to check.

    Returns:
        Tuple of (total_bytes, used_bytes, free_bytes).
    """
    stat = shutil.disk_usage(path)
    return stat.total, stat.used, stat.free
