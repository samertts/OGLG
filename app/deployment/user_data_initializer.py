"""User data directory initialization.

Creates and initializes the user data directory structure on first
application launch, including default configuration and database
initialization.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from app.utils.logger import get_logger

logger = get_logger("app.deployment.user_data_initializer")

_DEFAULT_CONFIG_FILENAME = "defaults.json"
_USER_CONFIG_FILENAME = "user_config.json"
_INIT_MARKER_FILENAME = ".initialized"


@dataclass
class InitResult:
    """Result of the user data initialization process.

    Attributes:
        success: Whether initialization completed without errors.
        directories_created: Directories that were newly created.
        files_created: Files that were newly created.
        existing: Paths that already existed before initialization.
        errors: Non-fatal errors encountered during initialization.
        warnings: Non-critical issues found during validation.
    """

    success: bool = False
    directories_created: list[str] = field(default_factory=list)
    files_created: list[str] = field(default_factory=list)
    existing: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class UserDataInitializer:
    """Creates and validates the user data directory structure.

    Responsible for first-run setup including directory creation,
    default configuration copying, and initialization marking.
    """

    def __init__(self, data_dirs: dict[str, Path]) -> None:
        """Initialize with the target data directories.

        Args:
            data_dirs: Mapping of logical names to Paths, typically
                from RuntimeLayout.directories.
        """
        self.data_dirs = data_dirs

    def initialize(self) -> InitResult:
        """Perform full initialization of user data directories.

        Creates directories, copies default config, and marks
        the environment as initialized.

        Returns:
            InitResult summarising everything that happened.
        """
        result = InitResult()

        dir_creation_result = self.create_directories()
        result.directories_created = dir_creation_result

        config_path = self.initialize_default_config()
        if config_path is not None:
            result.files_created.append(str(config_path))

        self.mark_initialized()
        result.files_created.append(str(self.get_first_run_marker()))

        validation = self.validate_initialized()
        if not validation.success:
            result.errors.extend(validation.errors)
            result.warnings.extend(validation.warnings)
            return result

        result.success = True
        logger.info("User data initialization complete")
        return result

    def create_directories(self) -> list[str]:
        """Create all configured data directories.

        Creates each directory with parents=True, exist_ok=True.
        Tracks which directories were newly created versus pre-existing.

        Returns:
            List of directory names that were newly created.
        """
        created: list[str] = []
        for name, path in self.data_dirs.items():
            if path.exists():
                continue
            path.mkdir(parents=True, exist_ok=True)
            created.append(name)
            logger.debug("Created directory", extra={"name": name, "path": str(path)})
        return created

    def initialize_default_config(self) -> Path | None:
        """Copy the bundled defaults.json to the user config directory.

        If the user_config.json already exists this is a no-op.

        Returns:
            Path to the created user config file, or None if it
            already existed or the source is missing.
        """
        config_dir = self.data_dirs.get("config")
        if config_dir is None:
            logger.warning("No config directory in data_dirs")
            return None

        user_config_path = config_dir / _USER_CONFIG_FILENAME
        if user_config_path.exists():
            logger.debug("User config already exists", extra={"path": str(user_config_path)})
            return None

        defaults_path = self._resolve_defaults_json()
        if defaults_path is None or not defaults_path.exists():
            logger.warning("Bundled defaults.json not found")
            return None

        try:
            config_dir.mkdir(parents=True, exist_ok=True)
            with defaults_path.open("r", encoding="utf-8") as src:
                config_data = json.load(src)
            with user_config_path.open("w", encoding="utf-8") as dst:
                json.dump(config_data, dst, indent=2, ensure_ascii=False)
            logger.info("Default config initialized", extra={"path": str(user_config_path)})
            return user_config_path
        except (OSError, json.JSONDecodeError) as exc:
            logger.error("Failed to initialize default config", extra={"error": str(exc)})
            return None

    def create_portable_marker(self) -> None:
        """Create the portable.txt marker in the data root directory.

        Only relevant when running in portable deployment mode.
        """
        portable_marker = self._get_data_root() / "portable.txt"
        portable_marker.write_text("portable\n", encoding="utf-8")
        logger.info("Portable marker created", extra={"path": str(portable_marker)})

    def is_first_run(self) -> bool:
        """Check whether this appears to be a first run.

        A first run is indicated by the absence of user_config.json
        and the absence of the .initialized marker.

        Returns:
            True if neither user_config.json nor .initialized exists.
        """
        config_dir = self.data_dirs.get("config")
        marker = self.get_first_run_marker()
        if config_dir is not None and (config_dir / _USER_CONFIG_FILENAME).exists():
            return False
        if marker.exists():
            return False
        return True

    def get_first_run_marker(self) -> Path:
        """Get the path to the .initialized marker file.

        Returns:
            Path to the .initialized file in the data root.
        """
        return self._get_data_root() / _INIT_MARKER_FILENAME

    def mark_initialized(self) -> None:
        """Create the .initialized marker file to record setup completion."""
        marker = self.get_first_run_marker()
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_text("initialized\n", encoding="utf-8")
        logger.info("Initialization marker created", extra={"path": str(marker)})

    def was_previously_initialized(self) -> bool:
        """Check whether the environment has been initialized before.

        Returns:
            True if the .initialized marker file exists.
        """
        return self.get_first_run_marker().exists()

    def validate_initialized(self) -> InitResult:
        """Verify that initialization is fully complete.

        Checks that all directories exist and that user_config.json
        is present.

        Returns:
            InitResult with validation findings.
        """
        result = InitResult()
        all_ok = True

        for name, path in self.data_dirs.items():
            if not path.is_dir():
                result.errors.append(f"Directory missing after init: {name}")
                all_ok = False

        config_dir = self.data_dirs.get("config")
        if config_dir is not None:
            user_config = config_dir / _USER_CONFIG_FILENAME
            if not user_config.exists():
                result.warnings.append("user_config.json not found after init")
                all_ok = False

        marker = self.get_first_run_marker()
        if not marker.exists():
            result.warnings.append("Initialization marker not found")
            all_ok = False

        result.success = all_ok
        return result

    def _get_data_root(self) -> Path:
        """Get the root data directory from the data_dirs mapping.

        Falls back to the parent of the first configured directory.

        Returns:
            The root data directory path.
        """
        if "root" in self.data_dirs:
            return self.data_dirs["root"]
        if self.data_dirs:
            return next(iter(self.data_dirs.values())).parent
        return Path()

    def _resolve_defaults_json(self) -> Path | None:
        """Resolve the path to the bundled defaults.json file.

        Tries to find it relative to common deployment layouts.

        Returns:
            Path to defaults.json, or None if resolution fails.
        """
        candidates = [
            Path(__file__).resolve().parent.parent / "config" / _DEFAULT_CONFIG_FILENAME,
            Path(__file__).resolve().parent.parent.parent
            / "app"
            / "config"
            / _DEFAULT_CONFIG_FILENAME,
        ]
        for candidate in candidates:
            if candidate.is_file():
                return candidate
        return None
