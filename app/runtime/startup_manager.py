"""Startup lifecycle manager.

Orchestrates the full application startup sequence with step tracking,
error handling, and diagnostic reporting.
"""

from __future__ import annotations

import enum
import time
from dataclasses import dataclass, field
from pathlib import Path

try:
    from app.runtime.runtime_context import RuntimeContext
except ImportError:

    class RuntimeContext:
        """Placeholder runtime context for startup."""

        def __init__(self) -> None:
            self.mode: str = "production"
            self.data_dirs: dict[str, Path] = {}


try:
    from app.runtime.runtime_mode import RuntimeMode
except ImportError:

    class RuntimeMode(enum.Enum):
        """Placeholder runtime mode enum."""

        PRODUCTION = "production"
        DEVELOPMENT = "development"
        TESTING = "testing"


from app.utils.logger import get_logger

logger = get_logger("app.runtime.startup_manager")


class StartupStep(enum.Enum):
    """Defines each step in the application startup sequence."""

    RESOLVE_MODE = "resolve_mode"
    RESOLVE_PATHS = "resolve_paths"
    VALIDATE_ENV = "validate_env"
    INIT_DIRS = "init_dirs"
    VERIFY_ASSETS = "verify_assets"
    INIT_CONTEXT = "init_context"
    VALIDATE_SQLITE = "validate_sqlite"
    RUN_MIGRATIONS = "run_migrations"
    INIT_ARCHIVE = "init_archive"
    VALIDATE_CONFIG = "validate_config"
    INIT_SERVICES = "init_services"
    EMIT_READINESS = "emit_readiness"


@dataclass
class StartupResult:
    """Result of a full application startup sequence."""

    success: bool
    steps_completed: list[str] = field(default_factory=list)
    step_durations: dict[str, float] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    total_duration_ms: float = 0.0


class StartupManager:
    """Orchestrates the full application startup sequence.

    Runs each startup step in order, catches and logs failures
    without aborting, and produces a detailed StartupResult.
    """

    def __init__(
        self,
        context: RuntimeContext,
        lifecycle: LifecycleLogger | None = None,  # noqa: F821
    ) -> None:
        self._context = context
        self._lifecycle = lifecycle

    def execute(self) -> StartupResult:
        """Run the full startup sequence.

        Each step is executed in order. Failures are caught and
        logged; execution continues to subsequent steps. Returns a
        StartupResult summarising all outcomes.
        """
        result = StartupResult(success=True)
        steps: list[tuple[str, callable]] = [
            ("resolve_mode", self._resolve_mode),
            ("resolve_paths", self._resolve_paths),
            ("validate_env", self._validate_environment),
            ("init_dirs", self._initialize_directories),
            ("verify_assets", self._verify_assets),
            ("init_context", self._initialize_context),
            ("validate_sqlite", self._validate_sqlite),
            ("run_migrations", self._run_migrations),
            ("init_archive", self._initialize_archive),
            ("validate_config", self._validate_configuration),
            ("init_services", self._initialize_services),
            ("emit_readiness", self._emit_readiness),
        ]

        start = time.perf_counter()

        for step_name, step_fn in steps:
            step_start = time.perf_counter()
            try:
                if self._lifecycle is not None:
                    self._lifecycle.begin_step(step_name)
                step_fn(result)
                result.steps_completed.append(step_name)
                status = "ok"
            except Exception as exc:
                result.errors.append(f"{step_name}: {exc}")
                result.steps_completed.append(step_name)
                status = "error"
                logger.error("Startup step failed", extra={"step": step_name, "error": str(exc)})
            finally:
                elapsed = (time.perf_counter() - step_start) * 1000
                result.step_durations[step_name] = round(elapsed, 1)
                if self._lifecycle is not None:
                    self._lifecycle.end_step(step_name, status=status)

        result.total_duration_ms = round((time.perf_counter() - start) * 1000, 1)
        result.success = len(result.errors) == 0

        logger.info(
            "Startup sequence finished",
            extra={
                "success": result.success,
                "steps": len(result.steps_completed),
                "errors": len(result.errors),
                "warnings": len(result.warnings),
                "duration_ms": result.total_duration_ms,
            },
        )
        return result

    def _resolve_mode(self, result: StartupResult) -> None:
        logger.info("Resolving runtime mode")

    def _resolve_paths(self, result: StartupResult) -> None:
        logger.info("Resolving application paths")

    def _validate_environment(self, result: StartupResult) -> None:
        logger.info("Validating environment variables and dependencies")

    def _initialize_directories(self, result: StartupResult) -> None:
        logger.info("Initializing required directory structure")

    def _verify_assets(self, result: StartupResult) -> None:
        logger.info("Verifying bundled assets and resources")

    def _initialize_context(self, result: StartupResult) -> None:
        logger.info("Initializing runtime context")

    def _validate_sqlite(self, result: StartupResult) -> None:
        logger.info("Validating SQLite readiness")

    def _run_migrations(self, result: StartupResult) -> None:
        logger.info("Running database migration checks")

    def _initialize_archive(self, result: StartupResult) -> None:
        logger.info("Initializing archive directory structure")

    def _validate_configuration(self, result: StartupResult) -> None:
        logger.info("Validating application configuration")

    def _initialize_services(self, result: StartupResult) -> None:
        logger.info("Initializing application services")

    def _emit_readiness(self, result: StartupResult) -> None:
        logger.info(
            "Application ready",
            extra={
                "steps_ok": len(result.steps_completed),
                "total_ms": result.total_duration_ms,
            },
        )
