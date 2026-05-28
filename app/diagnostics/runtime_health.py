"""Runtime health monitoring.

Provides health checks that can be called during application operation
to verify the system remains in a healthy state.
"""

from __future__ import annotations

import shutil
import sqlite3
import tempfile
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from pathlib import Path

from app.utils.logger import get_logger

logger = get_logger("app.diagnostics.runtime_health")


class HealthStatus(Enum):
    """Health status for a single runtime health check."""

    HEALTHY = auto()
    DEGRADED = auto()
    UNHEALTHY = auto()


@dataclass
class HealthCheckResult:
    """Result of a single runtime health check."""

    status: HealthStatus
    check_name: str
    message: str
    detail: str = ""
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class RuntimeContext:
    """Context information for runtime health monitoring.

    Captures the application's startup metadata and configured paths
    needed for ongoing health checks.
    """

    startup_time: datetime = field(default_factory=datetime.now)
    instance_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    data_dirs: dict[str, Path] = field(default_factory=dict)
    db_path: Path | None = None
    log_dir: Path | None = None


class RuntimeHealthMonitor:
    """Runtime health checks for ongoing application monitoring.

    Provides checks for database connectivity, disk space, temp directory,
    log directory writability, uptime, and session activity.

    Args:
        context: RuntimeContext with startup metadata and configured paths.
    """

    def __init__(self, context: RuntimeContext | None = None) -> None:
        self.context = context or RuntimeContext()

    def check_database_connectivity(self) -> HealthCheckResult:
        """Verify database connectivity by opening and closing a test connection.

        Returns:
            HealthCheckResult indicating database connectivity status.
        """
        if self.context.db_path is None:
            return HealthCheckResult(
                status=HealthStatus.UNHEALTHY,
                check_name="database_connectivity",
                message="Database path not configured",
                detail="No db_path provided in RuntimeContext",
            )
        try:
            parent = self.context.db_path.parent
            parent.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(str(self.context.db_path), timeout=5)
            conn.execute("SELECT 1;")
            conn.close()
            return HealthCheckResult(
                status=HealthStatus.HEALTHY,
                check_name="database_connectivity",
                message="Database connection successful",
                detail=f"Connected to {self.context.db_path}",
            )
        except sqlite3.Error as exc:
            return HealthCheckResult(
                status=HealthStatus.UNHEALTHY,
                check_name="database_connectivity",
                message=f"Database connection failed: {exc}",
                detail=str(exc),
            )

    def check_disk_space(self) -> HealthCheckResult:
        """Verify at least 200 MB free on each configured data directory.

        Returns:
            HealthCheckResult degraded if any directory is low on space.
        """
        warnings: list[str] = []
        for name, path in self.context.data_dirs.items():
            try:
                path.mkdir(parents=True, exist_ok=True)
                usage = shutil.disk_usage(path)
                free_mb = usage.free / (1024 * 1024)
                if free_mb < 200:
                    warnings.append(f"{name}: {free_mb:.0f} MB free < 200 MB")
            except OSError as exc:
                warnings.append(f"{name}: {exc}")

        if not warnings:
            return HealthCheckResult(
                status=HealthStatus.HEALTHY,
                check_name="disk_space",
                message="Sufficient disk space on all monitored directories",
                detail="All directories have >= 200 MB free",
            )

        return HealthCheckResult(
            status=HealthStatus.DEGRADED,
            check_name="disk_space",
            message="Low disk space on one or more directories",
            detail="; ".join(warnings),
        )

    def check_temp_directory(self) -> HealthCheckResult:
        """Verify the system temp directory is writable and not full.

        Checks for at least 50 MB free and write access.

        Returns:
            HealthCheckResult indicating temp directory status.
        """
        try:
            tmp = Path(tempfile.gettempdir())
            usage = shutil.disk_usage(tmp)
            free_mb = usage.free / (1024 * 1024)
            if free_mb < 50:
                return HealthCheckResult(
                    status=HealthStatus.DEGRADED,
                    check_name="temp_directory",
                    message=f"System temp directory low on space: {free_mb:.0f} MB free",
                    detail=f"Temp directory: {tmp}",
                )

            test_file = tmp / f".health_check_{uuid.uuid4().hex}"
            test_file.write_bytes(b"test")
            test_file.unlink()

            return HealthCheckResult(
                status=HealthStatus.HEALTHY,
                check_name="temp_directory",
                message="Temp directory is writable with sufficient space",
                detail=f"Temp directory: {tmp} ({free_mb:.0f} MB free)",
            )
        except OSError as exc:
            return HealthCheckResult(
                status=HealthStatus.UNHEALTHY,
                check_name="temp_directory",
                message=f"Temp directory check failed: {exc}",
                detail=str(exc),
            )

    def check_log_directory(self) -> HealthCheckResult:
        """Verify the log directory exists and is writable.

        Returns:
            HealthCheckResult indicating log directory writability.
        """
        log_dir = self.context.log_dir
        if log_dir is None:
            return HealthCheckResult(
                status=HealthStatus.UNHEALTHY,
                check_name="log_directory",
                message="Log directory not configured",
                detail="No log_dir provided in RuntimeContext",
            )
        try:
            log_dir.mkdir(parents=True, exist_ok=True)
            test_file = log_dir / ".health_log_write_test"
            test_file.write_bytes(b"test")
            test_file.unlink()
            return HealthCheckResult(
                status=HealthStatus.HEALTHY,
                check_name="log_directory",
                message="Log directory is writable",
                detail=str(log_dir),
            )
        except OSError as exc:
            return HealthCheckResult(
                status=HealthStatus.UNHEALTHY,
                check_name="log_directory",
                message=f"Log directory not writable: {exc}",
                detail=str(log_dir),
            )

    def check_uptime(self) -> HealthCheckResult:
        """Report the application uptime from the RuntimeContext.

        Returns:
            HealthCheckResult with uptime information.
        """
        uptime = datetime.now() - self.context.startup_time
        seconds = int(uptime.total_seconds())
        hours, remainder = divmod(seconds, 3600)
        minutes, secs = divmod(remainder, 60)

        uptime_str = f"{hours}h {minutes}m {secs}s" if hours else f"{minutes}m {secs}s"

        return HealthCheckResult(
            status=HealthStatus.HEALTHY,
            check_name="uptime",
            message=f"Uptime: {uptime_str}",
            detail="System running for extended period"
            if seconds >= 300
            else "System recently started",
        )

    def check_session_active(self) -> HealthCheckResult:
        """Verify the application session is active.

        Returns:
            HealthCheckResult indicating session activity.
        """
        uptime = datetime.now() - self.context.startup_time
        active = uptime.total_seconds() > 0
        return HealthCheckResult(
            status=HealthStatus.HEALTHY if active else HealthStatus.DEGRADED,
            check_name="session_active",
            message="Session is active" if active else "Session not yet started",
            detail=f"Instance ID: {self.context.instance_id}",
        )

    def run_scheduled_checks(self) -> list[HealthCheckResult]:
        """Run all non-intensive scheduled health checks.

        Excludes database connectivity (requires I/O) and includes
        disk space, temp directory, log directory, uptime, and
        session checks.

        Returns:
            List of HealthCheckResult for each scheduled check.
        """
        results: list[HealthCheckResult] = []
        results.append(self.check_disk_space())
        results.append(self.check_temp_directory())
        results.append(self.check_log_directory())
        results.append(self.check_uptime())
        results.append(self.check_session_active())
        return results

    def get_health_summary(self, results: list[HealthCheckResult]) -> dict:
        """Produce a summary dictionary from a list of health check results.

        Computes overall status (HEALTHY if all passed, DEGRADED if any
        degraded, UNHEALTHY if any unhealthy) and provides per-check details.

        Args:
            results: List of HealthCheckResult from one or more checks.

        Returns:
            Dictionary with overall_status, per-check details, and summary counts.
        """
        total = len(results)
        healthy = sum(1 for r in results if r.status == HealthStatus.HEALTHY)
        degraded = sum(1 for r in results if r.status == HealthStatus.DEGRADED)
        unhealthy = sum(1 for r in results if r.status == HealthStatus.UNHEALTHY)

        if total == 0:
            overall = HealthStatus.UNHEALTHY
        elif unhealthy > 0:
            overall = HealthStatus.UNHEALTHY
        elif degraded > 0:
            overall = HealthStatus.DEGRADED
        else:
            overall = HealthStatus.HEALTHY

        logger.info(
            "Health summary computed",
            extra={
                "overall": overall.name,
                "total": total,
                "healthy": healthy,
                "degraded": degraded,
                "unhealthy": unhealthy,
            },
        )

        return {
            "overall_status": overall.name,
            "checks": [
                {
                    "check_name": r.check_name,
                    "status": r.status.name,
                    "message": r.message,
                    "timestamp": r.timestamp.isoformat(),
                }
                for r in results
            ],
            "summary": {
                "total": total,
                "healthy": healthy,
                "degraded": degraded,
                "unhealthy": unhealthy,
            },
        }
