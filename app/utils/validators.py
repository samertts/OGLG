from __future__ import annotations

import re
from pathlib import Path
from typing import Any


def validate_required_string(value: Any, field_name: str, max_length: int = 500) -> str:
    """Validate a required string field.

    Args:
        value: The value to validate.
        field_name: Name of the field (for error messages).
        max_length: Maximum allowed length.

    Returns:
        The validated string.

    Raises:
        ValueError: If validation fails.
    """
    if not value or not isinstance(value, str):
        raise ValueError(f"{field_name} is required and must be a string")
    value = value.strip()
    if not value:
        raise ValueError(f"{field_name} cannot be empty")
    if len(value) > max_length:
        raise ValueError(
            f"{field_name} exceeds maximum length of {max_length} characters"
        )
    return value


def validate_optional_string(value: Any, field_name: str, max_length: int = 500) -> str | None:
    """Validate an optional string field.

    Args:
        value: The value to validate (or None).
        field_name: Name of the field (for error messages).
        max_length: Maximum allowed length.

    Returns:
        The validated string or None.
    """
    if value is None:
        return None
    return validate_required_string(value, field_name, max_length)


def validate_email(value: str | None) -> str | None:
    """Validate an email address.

    Args:
        value: Email string or None.

    Returns:
        Validated email or None.

    Raises:
        ValueError: If validation fails.
    """
    if value is None:
        return None
    pattern = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    if not pattern.match(value.strip()):
        raise ValueError(f"Invalid email address: {value}")
    return value.strip()


def validate_directory_exists(path: Path) -> Path:
    """Validate that a directory exists.

    Args:
        path: Directory path.

    Returns:
        The path if it exists.

    Raises:
        FileNotFoundError: If directory does not exist.
    """
    if not path.exists():
        raise FileNotFoundError(f"Directory not found: {path}")
    if not path.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {path}")
    return path


def validate_file_exists(path: Path) -> Path:
    """Validate that a file exists and is readable.

    Args:
        path: File path.

    Returns:
        The path if it exists.

    Raises:
        FileNotFoundError: If file does not exist.
    """
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    if not path.is_file():
        raise IsADirectoryError(f"Path is not a file: {path}")
    return path
