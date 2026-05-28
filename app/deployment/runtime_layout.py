"""Runtime directory layout definition.

Defines the complete directory structure required by the application
for both portable and installed deployment modes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from app.utils.logger import get_logger

logger = get_logger("app.deployment.runtime_layout")

_STANDARD_DIR_NAMES: list[str] = [
    "database",
    "archives",
    "backups",
    "generated_letters",
    "attachments",
    "logs",
    "temp",
    "config",
]


@dataclass
class RuntimeLayout:
    """Defines the complete runtime directory structure.

    Attributes:
        root: The data root directory.
        directories: Mapping of directory names to their resolved paths.
    """

    root: Path
    directories: dict[str, Path] = field(default_factory=dict)

    def ensure_all(self) -> None:
        """Create all configured directories and their parents."""
        for name, path in self.directories.items():
            path.mkdir(parents=True, exist_ok=True)
            logger.debug("Ensured directory exists", extra={"name": name, "path": str(path)})

    def validate_all(self) -> bool:
        """Verify that all configured directories exist on disk.

        Returns:
            True if every directory exists, False otherwise.
        """
        missing: list[str] = []
        for name, path in self.directories.items():
            if not path.is_dir():
                missing.append(name)
        if missing:
            logger.warning("Layout validation failed", extra={"missing": missing})
            return False
        return True

    def get_size_bytes(self) -> int:
        """Compute the total disk usage of all directories recursively.

        Returns:
            Total size in bytes.
        """
        total = 0
        for path in self.directories.values():
            if not path.exists():
                continue
            for f in path.rglob("*"):
                if f.is_file():
                    try:
                        total += f.stat().st_size
                    except OSError:
                        continue
        return total

    def list_contents(self) -> dict[str, list[str]]:
        """List all files and directories inside each managed directory.

        Returns:
            Dictionary mapping directory names to their child entries
            relative to that directory.
        """
        contents: dict[str, list[str]] = {}
        for name, path in self.directories.items():
            if path.is_dir():
                contents[name] = [str(p.relative_to(path)) for p in sorted(path.iterdir())]
            else:
                contents[name] = []
        return contents


def create_runtime_layout(root: Path) -> RuntimeLayout:
    """Create a RuntimeLayout with the standard directory structure.

    Args:
        root: The root data directory.

    Returns:
        A fully populated RuntimeLayout instance.
    """
    directories = get_standard_layout(root)
    return RuntimeLayout(root=root, directories=directories)


def get_standard_layout(root: Path) -> dict[str, Path]:
    """Return the standard directory mapping for a given root.

    Args:
        root: The root data directory.

    Returns:
        Dictionary mapping standard directory names to their paths.
    """
    return {name: root / name for name in _STANDARD_DIR_NAMES}


def is_layout_complete(layout: RuntimeLayout) -> tuple[bool, list[str]]:
    """Check which directories from the layout are present.

    Args:
        layout: The RuntimeLayout to inspect.

    Returns:
        Tuple of (all_present, list_of_missing_directory_names).
    """
    missing: list[str] = []
    for name, path in layout.directories.items():
        if not path.is_dir():
            missing.append(name)
    return len(missing) == 0, missing
