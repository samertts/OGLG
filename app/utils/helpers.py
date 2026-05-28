from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    """Load and parse a JSON file.

    Args:
        path: Path to the JSON file.

    Returns:
        Parsed dictionary.

    Raises:
        FileNotFoundError: If file not found.
        json.JSONDecodeError: If file is not valid JSON.
    """
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: dict[str, Any], atomic: bool = True) -> None:
    """Save data as JSON to a file.

    Args:
        path: Path to the output file.
        data: Data to serialize.
        atomic: If True, use atomic write.
    """
    content = json.dumps(data, indent=2, ensure_ascii=False, default=str).encode("utf-8")
    if atomic:
        from app.utils.file_utils import atomic_write
        atomic_write(path, content)
    else:
        path.write_bytes(content)


def format_timestamp(dt: datetime | None) -> str | None:
    """Format a datetime to ISO 8601 string.

    Args:
        dt: Datetime to format.

    Returns:
        ISO 8601 formatted string or None.
    """
    if dt is None:
        return None
    return dt.isoformat()


def parse_timestamp(value: str | None) -> datetime | None:
    """Parse an ISO 8601 string to datetime.

    Args:
        value: ISO 8601 formatted string.

    Returns:
        Datetime or None.
    """
    if not value:
        return None
    return datetime.fromisoformat(value)


def sanitize_filename(name: str) -> str:
    """Remove unsafe characters from a filename.

    Args:
        name: Original filename.

    Returns:
        Sanitized filename safe for filesystem use.
    """
    import re
    safe = re.sub(r'[\\/:*?"<>|\x00-\x1f]', "_", name)
    safe = safe.strip("._")
    if len(safe) > 200:
        stem, ext = Path(safe).stem, Path(safe).suffix
        safe = stem[:195] + ext
    return safe or "unnamed"
