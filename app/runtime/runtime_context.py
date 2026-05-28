"""Runtime context holding shared application state.

Provides a single source of truth for the current runtime mode,
resolved paths, and application lifecycle state.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from app.runtime.path_resolver import create_path_resolver
from app.runtime.runtime_mode import RuntimeMode
from app.utils.logger import get_logger

logger = get_logger("app.runtime.runtime_context")


@dataclass(frozen=True)
class RuntimeContext:
    """Immutable container for all runtime environment state.

    Attributes:
        mode: The detected runtime deployment mode.
        app_root: Resolved application root directory.
        data_dir: Root data directory for user-generated content.
        config_dir: Directory for configuration files.
        database_dir: Directory for the SQLite database.
        logs_dir: Directory for application log files.
        temp_dir: Directory for temporary files.
        backups_dir: Directory for backup archives.
        archives_dir: Directory for archival storage.
        assets_dir: Directory for bundled application assets.
        fonts_dir: Directory for bundled fonts.
        templates_dir: Directory for bundled templates.
        startup_timestamp: Timestamp when this context was created.
        instance_id: Unique identifier for this application instance.
    """

    mode: RuntimeMode
    app_root: Path
    data_dir: Path
    config_dir: Path
    database_dir: Path
    logs_dir: Path
    temp_dir: Path
    backups_dir: Path
    archives_dir: Path
    assets_dir: Path
    fonts_dir: Path
    templates_dir: Path
    startup_timestamp: datetime = field(default_factory=datetime.now)
    instance_id: str = field(default_factory=lambda: uuid4().hex)


_current_context: RuntimeContext | None = None


def get_current_context() -> RuntimeContext:
    """Retrieve the current runtime context.

    Returns:
        The active RuntimeContext instance.

    Raises:
        RuntimeError: If the context has not been initialized.
    """
    if _current_context is None:
        raise RuntimeError(
            "RuntimeContext has not been initialized. Call set_current_context() during bootstrap."
        )
    return _current_context


def set_current_context(ctx: RuntimeContext) -> None:
    """Set the current runtime context (called during bootstrap).

    Args:
        ctx: The RuntimeContext instance to set as active.
    """
    global _current_context  # noqa: PLW0603
    _current_context = ctx
    logger.info(
        "Runtime context set",
        extra={"mode": ctx.mode.value, "instance_id": ctx.instance_id},
    )


def create_runtime_context(
    mode: RuntimeMode,
    data_dir_override: Path | None = None,
) -> RuntimeContext:
    """Create a fully resolved RuntimeContext.

    Resolves all required paths using PathResolver based on the provided
    runtime mode.

    Args:
        mode: The RuntimeMode to use for path resolution.
        data_dir_override: Optional data directory override.

    Returns:
        A fully populated RuntimeContext instance.
    """
    resolver = create_path_resolver(mode=mode, data_dir_override=data_dir_override)
    all_dirs = resolver.get_all_directories()

    ctx = RuntimeContext(
        mode=mode,
        app_root=resolver.app_root,
        data_dir=all_dirs["data"],
        config_dir=all_dirs["config"],
        database_dir=all_dirs["database"],
        logs_dir=all_dirs["logs"],
        temp_dir=all_dirs["temp"],
        backups_dir=all_dirs["backups"],
        archives_dir=all_dirs["archives"],
        assets_dir=all_dirs["assets"],
        fonts_dir=all_dirs["fonts"],
        templates_dir=all_dirs["templates"],
    )

    logger.info(
        "Runtime context created",
        extra={
            "mode": mode.value,
            "app_root": str(ctx.app_root),
            "data_dir": str(ctx.data_dir),
            "instance_id": ctx.instance_id,
        },
    )

    return ctx
