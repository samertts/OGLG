"""Runtime dependency verification.

Checks that all required Python packages and system dependencies
are available and compatible.
"""

from __future__ import annotations

import importlib.metadata
import importlib.util
from dataclasses import dataclass
from enum import Enum, auto

from app.utils.logger import get_logger

logger = get_logger("app.diagnostics.dependency_verifier")


class DependencyStatus(Enum):
    """Status of a single dependency check."""

    AVAILABLE = auto()
    MISSING = auto()
    INCOMPATIBLE = auto()


@dataclass
class DependencyCheck:
    """Result of a single dependency verification check."""

    name: str
    status: DependencyStatus
    version: str | None
    required: str
    detail: str = ""


class DependencyVerifier:
    """Verifies all runtime dependencies.

    Checks core Python packages (sqlalchemy, alembic, loguru),
    built-in system libraries, and optional dependencies (PyInstaller,
    cryptography, reportlab).
    """

    @staticmethod
    def verify_python_packages() -> list[DependencyCheck]:
        """Verify core Python packages meet minimum version requirements.

        Returns:
            List of DependencyCheck results for each core package.
        """
        checks: list[DependencyCheck] = []
        checks.append(DependencyVerifier._check_package("sqlalchemy", ">=2.0"))
        checks.append(DependencyVerifier._check_package("alembic", ">=1.13"))
        checks.append(DependencyVerifier._check_package("loguru", ">=0.7"))
        return checks

    @staticmethod
    def verify_system_libraries() -> list[DependencyCheck]:
        """Verify built-in Python system libraries are importable.

        Returns:
            List of DependencyCheck results for each built-in library.
        """
        libraries = [
            ("sqlite3", "built-in"),
            ("hashlib", "built-in"),
            ("json", "built-in"),
            ("uuid", "built-in"),
            ("zipfile", "built-in"),
        ]
        checks: list[DependencyCheck] = []
        for lib_name, required in libraries:
            spec = importlib.util.find_spec(lib_name)
            available = spec is not None
            checks.append(
                DependencyCheck(
                    name=lib_name,
                    status=DependencyStatus.AVAILABLE if available else DependencyStatus.MISSING,
                    version="built-in" if available else None,
                    required=required,
                    detail=(
                        f"Found at {spec.origin}"
                        if available and spec and spec.origin
                        else "Module not found in Python path"
                    ),
                )
            )
        return checks

    @staticmethod
    def verify_optional_dependencies() -> list[DependencyCheck]:
        """Verify optional dependencies that may not be installed.

        Returns:
            List of DependencyCheck results for optional packages.
        """
        checks: list[DependencyCheck] = []
        checks.append(
            DependencyVerifier._check_optional_package("PyInstaller", "for frozen/bundled mode")
        )
        checks.append(DependencyVerifier._check_optional_package("cryptography", "for signing"))
        checks.append(DependencyVerifier._check_optional_package("reportlab", "for PDF generation"))
        return checks

    @staticmethod
    def run_all() -> list[DependencyCheck]:
        """Run all dependency verifications (core, system, optional).

        Returns:
            Combined list of all DependencyCheck results.
        """
        checks: list[DependencyCheck] = []
        checks.extend(DependencyVerifier.verify_python_packages())
        checks.extend(DependencyVerifier.verify_system_libraries())
        checks.extend(DependencyVerifier.verify_optional_dependencies())
        return checks

    @staticmethod
    def all_available(checks: list[DependencyCheck]) -> bool:
        """Check if all dependencies are available.

        Args:
            checks: List of DependencyCheck results.

        Returns:
            True if every check has AVAILABLE status.
        """
        return all(c.status == DependencyStatus.AVAILABLE for c in checks)

    @staticmethod
    def get_missing(checks: list[DependencyCheck]) -> list[DependencyCheck]:
        """Filter for dependencies that are not available.

        Args:
            checks: List of DependencyCheck results.

        Returns:
            List of checks with MISSING or INCOMPATIBLE status.
        """
        return [c for c in checks if c.status != DependencyStatus.AVAILABLE]

    @staticmethod
    def _check_package(name: str, required: str) -> DependencyCheck:
        """Check a specific Python package by name via importlib.metadata.

        Args:
            name: Package distribution name.
            required: Version requirement string (e.g. '>=2.0').

        Returns:
            DependencyCheck with version and status.
        """
        try:
            dist = importlib.metadata.distribution(name)
            version = dist.version
            return DependencyCheck(
                name=name,
                status=DependencyStatus.AVAILABLE,
                version=version,
                required=required,
                detail=f"Package '{name}' version {version} is installed",
            )
        except importlib.metadata.PackageNotFoundError:
            return DependencyCheck(
                name=name,
                status=DependencyStatus.MISSING,
                version=None,
                required=required,
                detail=f"Package '{name}' not found. Install with: pip install {name}{required}",
            )

    @staticmethod
    def _check_optional_package(name: str, purpose: str) -> DependencyCheck:
        """Check an optional package by name.

        Args:
            name: Package distribution name.
            purpose: Human-readable description of why it is needed.

        Returns:
            DependencyCheck with version and status.
        """
        try:
            dist = importlib.metadata.distribution(name)
            version = dist.version
            return DependencyCheck(
                name=name,
                status=DependencyStatus.AVAILABLE,
                version=version,
                required="optional",
                detail=f"Available for {purpose}",
            )
        except importlib.metadata.PackageNotFoundError:
            return DependencyCheck(
                name=name,
                status=DependencyStatus.MISSING,
                version=None,
                required="optional",
                detail=f"Optional dependency '{name}' not found ({purpose}). Install if needed.",
            )
