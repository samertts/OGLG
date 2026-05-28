"""Bootstrap / DI container for the Correspondence System.

Provides factory functions and a container that wires all dependencies
together for clean startup and testability.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from sqlalchemy.orm import Session

from app.config.settings import Settings, load_settings
from app.database.connection import DatabaseManager
from app.database.repositories import (
    SQLAlchemyAttachmentRepository,
    SQLAlchemyAuditRepository,
    SQLAlchemyBackupRepository,
    SQLAlchemyDepartmentRepository,
    SQLAlchemyLetterRepository,
    SQLAlchemyUserRepository,
)
from app.runtime.lifecycle import LifecycleLogger
from app.services import AuditService, BackupService, LetterService
from app.utils.file_utils import cleanup_temp_files
from app.utils.logger import configure_logging, get_logger
from app.utils.paths import (
    ensure_data_directories,
    get_config_path,
    get_default_config_path,
    resolve_data_directory,
)

logger = get_logger("app.bootstrap")


@dataclass
class Container:
    """Application container holding all wired dependencies."""

    settings: Settings
    db_manager: DatabaseManager
    letter_repo: SQLAlchemyLetterRepository
    user_repo: SQLAlchemyUserRepository
    department_repo: SQLAlchemyDepartmentRepository
    attachment_repo: SQLAlchemyAttachmentRepository
    audit_repo: SQLAlchemyAuditRepository
    backup_repo: SQLAlchemyBackupRepository
    audit_service: AuditService
    backup_service: BackupService
    letter_service: LetterService
    data_dirs: dict[str, Path]

    def get_session(self) -> Session:
        if not self.db_manager.session_factory:
            raise RuntimeError("Database not initialized")
        return self.db_manager.session_factory()

    def close(self) -> None:
        self.db_manager.dispose()
        logger.info("Container shut down")


def build_container(
    portable: bool = False,
    data_dir_override: str | None = None,
    log_level: str | None = None,
    db_pool_size: int | None = None,
    db_timeout: int | None = None,
    lifecycle: LifecycleLogger | None = None,
) -> Container:
    """Build and wire the full application container.

    Args:
        portable: Run in portable mode (data next to executable).
        data_dir_override: Explicit data directory path.
        log_level: Override log level.
        db_pool_size: Override database pool size.
        db_timeout: Override database timeout in seconds.
        lifecycle: Optional LifecycleLogger for step tracking.

    Returns:
        Fully wired Container instance.
    """
    if lifecycle:
        lifecycle.begin_step("resolve_data_dir")

    resolved_data_dir: Path
    if data_dir_override:
        resolved_data_dir = Path(data_dir_override).resolve()
    else:
        resolved_data_dir = resolve_data_directory(portable=portable)

    if lifecycle:
        lifecycle.end_step("resolve_data_dir", "ok")
        lifecycle.begin_step("load_settings")

    defaults_path = get_default_config_path()
    user_config_path = get_config_path(resolved_data_dir)

    settings = load_settings(
        defaults_path=defaults_path,
        user_config_path=user_config_path if user_config_path.exists() else None,
        data_dir=resolved_data_dir,
    )

    if log_level:
        settings.log_level = log_level
    if db_pool_size is not None:
        settings.db_pool_size = db_pool_size
    if db_timeout is not None:
        settings.db_timeout = db_timeout

    if lifecycle:
        lifecycle.end_step("load_settings", "ok")
        lifecycle.begin_step("ensure_data_dirs")

    data_dirs = ensure_data_directories(resolved_data_dir)

    if lifecycle:
        lifecycle.end_step("ensure_data_dirs", "ok")
        lifecycle.begin_step("configure_logging")

    configure_logging(
        log_dir=data_dirs["logs"],
        level=settings.log_level,
        rotation=settings.log_rotation,
        retention=settings.log_retention,
        json_format=settings.log_json_format,
    )

    if lifecycle:
        lifecycle.end_step("configure_logging", "ok")
        lifecycle.begin_step("init_database")

    cleanup_temp_files(data_dirs["temp"])

    db_manager = DatabaseManager(
        db_path=data_dirs["database"] / "correspondence.db",
        pool_size=settings.db_pool_size,
        timeout=settings.db_timeout,
    )
    db_manager.initialize()

    if lifecycle:
        lifecycle.end_step("init_database", "ok")
        lifecycle.begin_step("run_migrations")

    _run_migrations(db_manager)

    if lifecycle:
        lifecycle.end_step("run_migrations", "ok")
        lifecycle.begin_step("verify_integrity")

    if not db_manager.verify_integrity():
        logger.warning("Database integrity check failed — attempting recovery")
        _attempt_recovery(db_manager)

    if lifecycle:
        lifecycle.end_step("verify_integrity", "ok")
        lifecycle.begin_step("instantiate_repos")

    session = db_manager.session_factory()

    letter_repo = SQLAlchemyLetterRepository(session)
    user_repo = SQLAlchemyUserRepository(session)
    department_repo = SQLAlchemyDepartmentRepository(session)
    attachment_repo = SQLAlchemyAttachmentRepository(session)
    audit_repo = SQLAlchemyAuditRepository(session)
    backup_repo = SQLAlchemyBackupRepository(session)

    if lifecycle:
        lifecycle.end_step("instantiate_repos", "ok")
        lifecycle.begin_step("instantiate_services")

    audit_service = AuditService(audit_repo=audit_repo)
    backup_service = BackupService(
        backup_repo=backup_repo,
        db_manager=db_manager,
        backup_dir=data_dirs["backups"],
    )
    letter_service = LetterService(letter_repo=letter_repo)

    if lifecycle:
        lifecycle.end_step("instantiate_services", "ok")

    logger.info("Application container built successfully")
    return Container(
        settings=settings,
        db_manager=db_manager,
        letter_repo=letter_repo,
        user_repo=user_repo,
        department_repo=department_repo,
        attachment_repo=attachment_repo,
        audit_repo=audit_repo,
        backup_repo=backup_repo,
        audit_service=audit_service,
        backup_service=backup_service,
        letter_service=letter_service,
        data_dirs=data_dirs,
    )


def _run_migrations(db_manager: DatabaseManager) -> None:
    """Run pending Alembic migrations on startup.

    Uses a subprocess call to alembic for simplicity. Falls back
    gracefully if alembic is not available or migrations fail.
    """
    from alembic import command
    from alembic.config import Config

    from app.utils.paths import get_migrations_dir

    try:
        migrations_dir = get_migrations_dir()
        alembic_cfg = Config(str(migrations_dir / "alembic.ini"))
        alembic_cfg.set_main_option("script_location", str(migrations_dir))
        alembic_cfg.set_main_option(
            "sqlalchemy.url",
            f"sqlite:///{db_manager.db_path.resolve()}",
        )
        command.upgrade(alembic_cfg, "head")
        logger.info("Database migrations up to date")
    except Exception as exc:
        logger.warning("Migration error (non-fatal)", extra={"error": str(exc)})


def _attempt_recovery(db_manager: DatabaseManager) -> None:
    """Attempt basic database recovery.

    If integrity check fails, try VACUUM and recheck. This handles
    the most common SQLite corruption scenarios.
    """
    try:
        db_manager.vacuum()
        logger.info("Vacuum completed as part of recovery attempt")
    except Exception as exc:
        logger.error("Vacuum recovery failed", extra={"error": str(exc)})
