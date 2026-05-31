"""Main entry point for the Correspondence System.

Startup lifecycle (13 steps):
  1. Parse CLI arguments
  2. Detect deployment mode (portable / installed / development)
  3. Run deployment validation (directory structure, disk space, fonts)
  4. Register bundled Arabic fonts
  5. Configure logging
  6. Load settings from all tiers
  7. Ensure data directory structure
  8. Initialize SQLite database engine
  9. Run database migrations
  10. Crash recovery / integrity check
  11. Instantiate repository implementations
  12. Instantiate application services
  13. Enter application event loop
"""

from __future__ import annotations

import argparse
import signal
import sys
from typing import NoReturn

from app.bootstrap import Container, build_container
from app.deployment.fonts import register_application_fonts
from app.deployment.validation import run_startup_validation
from app.diagnostics.environment import EnvironmentVerifier
from app.diagnostics.readiness import DeploymentReadinessValidator
from app.diagnostics.startup import StartupDiagnosticsEngine
from app.runtime.archive import ArchiveDirectoryInitializer
from app.runtime.cleanup import TempCleanupEngine
from app.runtime.lifecycle import LifecycleLogger
from app.runtime.recovery import CrashRecoveryBootstrap
from app.runtime.state import RuntimeState, RuntimeStateMachine
from app.utils.logger import get_logger

logger = get_logger("app.main")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="oglg",
        description="Iraqi Government Offline Official Correspondence System",
    )
    parser.add_argument(
        "--portable",
        action="store_true",
        help="Run in portable mode (data next to executable)",
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default=None,
        help="Explicit data directory path",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default=None,
        help="Override log level",
    )
    parser.add_argument(
        "--db-pool-size",
        type=int,
        default=None,
        help="Database connection pool size",
    )
    parser.add_argument(
        "--db-timeout",
        type=int,
        default=None,
        help="Database connection timeout in seconds",
    )
    parser.add_argument(
        "--version",
        action="store_true",
        help="Show version and exit",
    )
    parser.add_argument(
        "--skip-validation",
        action="store_true",
        help="Skip startup validation checks",
    )
    return parser.parse_args(argv)


def show_version() -> NoReturn:
    from app import __app_name__, __org_name__, __version__

    print(f"{__app_name__} v{__version__}")
    print(f"{__org_name__}")
    sys.exit(0)


def setup_signal_handlers(
    container: Container,
    state_machine: RuntimeStateMachine,
) -> None:
    def shutdown(signum: int, frame: object) -> None:
        logger.info("Shutdown signal received", extra={"signal": signum})
        try:
            state_machine.transition_to(RuntimeState.SHUTTING_DOWN)
        except Exception:
            pass
        container.close()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)


def main(argv: list[str] | None = None) -> None:
    lifecycle = LifecycleLogger()
    state_machine = RuntimeStateMachine()

    lifecycle.begin_step("cli_args")
    args = parse_args(argv)
    lifecycle.end_step("cli_args", "ok")

    if args.version:
        show_version()

    portable = args.portable or False
    data_dir_override = args.data_dir
    skip_validation = args.skip_validation or False

    state_machine.transition_to(RuntimeState.INITIALIZING)

    lifecycle.begin_step("deployment_validation")
    if not skip_validation:
        validation_result = run_startup_validation(portable=portable)
        if not validation_result.passed:
            logger.error(
                "Startup validation failed — aborting",
                extra={"errors": validation_result.errors},
            )
            print("ERROR: Deployment validation failed:", file=sys.stderr)
            for err in validation_result.errors:
                print(f"  - {err}", file=sys.stderr)
            sys.exit(1)
        for warning in validation_result.warnings:
            logger.warning("Startup warning", extra={"warning": warning})
    lifecycle.end_step("deployment_validation", "ok")

    state_machine.transition_to(RuntimeState.VALIDATING)

    if portable:
        lifecycle.begin_step("font_registration")
        register_application_fonts()
        lifecycle.end_step("font_registration", "ok")

    lifecycle.begin_step("build_container")
    container = build_container(
        portable=portable,
        data_dir_override=data_dir_override,
        log_level=args.log_level,
        db_pool_size=args.db_pool_size,
        db_timeout=args.db_timeout,
        lifecycle=lifecycle,
    )
    lifecycle.end_step("build_container", "ok")

    lifecycle.begin_step("diagnostics")
    env_verifier = EnvironmentVerifier(
        data_dirs=list(container.data_dirs.values()),
    )
    readiness_validator = DeploymentReadinessValidator(
        paths=container.data_dirs,
    )
    diagnostics_engine = StartupDiagnosticsEngine(
        env_verifier=env_verifier,
        readiness_validator=readiness_validator,
        lifecycle=lifecycle,
    )
    diagnostics_result = diagnostics_engine.run_diagnostics()
    if not diagnostics_result["ready"]:
        logger.warning(
            "Deployment readiness issues detected",
            extra={
                "score": diagnostics_result["readiness"]["readiness_score"],
                "critical": diagnostics_result["readiness"]["critical_failures"],
            },
        )
    lifecycle.end_step("diagnostics", "ok")

    lifecycle.begin_step("crash_recovery")
    recovery_bootstrap = CrashRecoveryBootstrap(
        data_dirs=container.data_dirs,
        db_path=container.settings.database_path,
    )
    recovery_result = recovery_bootstrap.run_recovery()
    if recovery_result.recovered:
        logger.info(
            "Recovery actions performed",
            extra={
                "integrity_ok": recovery_result.integrity_ok,
                "temp_cleaned": recovery_result.temp_files_cleaned,
                "lock_cleared": recovery_result.stale_lock_cleared,
            },
        )
    recovery_bootstrap.write_lock()
    lifecycle.end_step("crash_recovery", "ok")

    lifecycle.begin_step("archive_init")
    archive_dir = container.data_dirs.get("archives")
    if archive_dir:
        archive_init = ArchiveDirectoryInitializer(archive_dir)
        archive_result = archive_init.initialize()
        if archive_result.errors:
            logger.warning("Archive init had errors", extra={"errors": archive_result.errors})
    lifecycle.end_step("archive_init", "ok")

    lifecycle.begin_step("temp_cleanup")
    temp_dir = container.data_dirs.get("temp")
    log_dir = container.data_dirs.get("logs")
    if temp_dir:
        cleanup_engine = TempCleanupEngine(
            temp_dir=temp_dir,
            log_dir=log_dir,
        )
        cleanup_engine.run_cleanup()
    lifecycle.end_step("temp_cleanup", "ok")

    state_machine.transition_to(RuntimeState.STARTING)

    setup_signal_handlers(container, state_machine)

    state_machine.transition_to(RuntimeState.RUNNING)

    lifecycle.print_summary()

    logger.info(
        "Application started",
        extra={
            "version": container.settings.app_version,
            "data_dir": str(container.settings.data_dir),
            "log_level": container.settings.log_level,
            "deploy_mode": args.portable or "installed",
            "state": state_machine.current.value,
        },
    )

    try:
        from PySide6.QtWidgets import QApplication

        qt_app = QApplication(sys.argv)
        qt_app.setApplicationName("oglg")
        qt_app.setOrganizationName("IraqiGovernment")
        qt_app.setApplicationVersion(container.settings.app_version)

        from app.ui.app import launch_ui

        launch_ui(qt_app, container, rtl=True)
        sys.exit(qt_app.exec())
    except ImportError:
        logger.info("No GUI module found — running in headless mode")
        _run_headless_event_loop(container, state_machine, recovery_bootstrap)


def _run_headless_event_loop(
    container: Container,
    state_machine: RuntimeStateMachine,
    recovery_bootstrap: CrashRecoveryBootstrap | None = None,
) -> None:
    """Run a simple headless event loop for CLI/server mode."""
    import time

    logger.info("Headless mode — idle loop (press Ctrl+C to exit)")
    try:
        while state_machine.is_running:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutdown requested")
    finally:
        try:
            state_machine.transition_to(RuntimeState.SHUTTING_DOWN)
        except Exception:
            pass
        if recovery_bootstrap:
            recovery_bootstrap.clear_lock()
        container.close()
        try:
            state_machine.transition_to(RuntimeState.STOPPED)
        except Exception:
            pass


if __name__ == "__main__":
    main()
