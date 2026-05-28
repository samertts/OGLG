"""Asset validation for bundled resources.

Validates that all required application assets (fonts, templates,
config files) are present and have correct checksums.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path

from app.utils.logger import get_logger

logger = get_logger("app.deployment.asset_validator")


@dataclass
class AssetValidationResult:
    """Result of a full or partial asset validation pass.

    Attributes:
        all_valid: True if all required assets passed validation.
        valid: Relative paths of assets that passed.
        missing: Relative paths of required assets not found on disk.
        corrupted: Relative paths of assets with hash mismatch.
        errors: Non-specific errors encountered during validation.
    """

    all_valid: bool = False
    valid: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)
    corrupted: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


@dataclass
class AssetEntry:
    """Describes a single asset file in the bundle.

    Attributes:
        relative_path: Path relative to the application root.
        expected_hash: Optional SHA-256 hex digest for integrity check.
        required: If True, a missing asset is treated as an error.
    """

    relative_path: str
    expected_hash: str | None = None
    required: bool = True


class AssetValidator:
    """Validates bundled assets required for application operation.

    Scans the application bundle for fonts, templates, configuration,
    and migration files, optionally verifying their SHA-256 hashes.
    """

    def __init__(self, app_root: Path) -> None:
        """Initialize the validator with the application root.

        Args:
            app_root: The root directory of the application bundle.
        """
        self.app_root = app_root.resolve()

    def validate_all(self) -> AssetValidationResult:
        """Validate all required application assets.

        Combines results from fonts, templates, config, and migrations
        validation into a single report.

        Returns:
            Aggregate AssetValidationResult.
        """
        fonts_result = self.validate_fonts()
        templates_result = self.validate_templates()
        config_result = self.validate_config()
        migrations_result = self.validate_migrations()

        combined = AssetValidationResult()
        for sub in (fonts_result, templates_result, config_result, migrations_result):
            combined.valid.extend(sub.valid)
            combined.missing.extend(sub.missing)
            combined.corrupted.extend(sub.corrupted)
            combined.errors.extend(sub.errors)

        combined.all_valid = not combined.missing and not combined.corrupted and not combined.errors
        return combined

    def validate_fonts(self) -> AssetValidationResult:
        """Validate all fonts in the bundled fonts directory.

        Returns:
            AssetValidationResult for font assets.
        """
        result = AssetValidationResult()
        font_dir = self.app_root / "assets" / "fonts"
        if not font_dir.is_dir():
            result.errors.append("Fonts directory not found")
            return result

        for entry in self._get_font_entries():
            self._validate_entry(entry, result)

        if result.missing or result.corrupted:
            logger.warning(
                "Font validation found issues",
                extra={"missing": result.missing, "corrupted": result.corrupted},
            )
        return result

    def validate_templates(self) -> AssetValidationResult:
        """Validate all templates in the bundled templates directory.

        Returns:
            AssetValidationResult for template assets.
        """
        result = AssetValidationResult()
        templates_dir = self.app_root / "assets" / "templates"
        if not templates_dir.is_dir():
            result.errors.append("Templates directory not found")
            return result

        for entry in self._get_template_entries():
            self._validate_entry(entry, result)

        if result.missing or result.corrupted:
            logger.warning(
                "Template validation found issues",
                extra={"missing": result.missing, "corrupted": result.corrupted},
            )
        return result

    def validate_config(self) -> AssetValidationResult:
        """Validate the bundled defaults.json configuration file.

        Returns:
            AssetValidationResult for the default config asset.
        """
        result = AssetValidationResult()
        config_path = self.app_root / "app" / "config" / "defaults.json"
        if config_path.is_file():
            result.valid.append("app/config/defaults.json")
        else:
            result.missing.append("app/config/defaults.json")
            logger.warning("Default config file missing")
        return result

    def validate_migrations(self) -> AssetValidationResult:
        """Validate the Alembic migrations directory.

        Returns:
            AssetValidationResult for migration assets.
        """
        result = AssetValidationResult()
        migrations_dir = self.app_root / "app" / "database" / "migrations"
        if not migrations_dir.is_dir():
            result.errors.append("Migrations directory not found")
            return result

        for entry in self._get_migration_entries():
            self._validate_entry(entry, result)

        if result.missing or result.corrupted:
            logger.warning(
                "Migration validation found issues",
                extra={
                    "missing": result.missing,
                    "corrupted": result.corrupted,
                },
            )
        return result

    def _check_file_exists(self, relative: str) -> bool:
        """Check whether a bundled asset file exists on disk.

        Args:
            relative: Asset path relative to the application root.

        Returns:
            True if the file exists.
        """
        return (self.app_root / relative).is_file()

    def _check_file_hash(self, relative: str, expected: str) -> bool:
        """Verify a file's SHA-256 hash matches the expected value.

        Args:
            relative: Asset path relative to the application root.
            expected: Expected SHA-256 hex digest.

        Returns:
            True if the hash matches or the file is missing.
        """
        file_path = self.app_root / relative
        if not file_path.is_file():
            return False
        try:
            sha256 = hashlib.sha256()
            with file_path.open("rb") as f:
                for chunk in iter(lambda: f.read(65536), b""):
                    sha256.update(chunk)
            return sha256.hexdigest() == expected
        except OSError:
            return False

    def _validate_entry(self, entry: AssetEntry, result: AssetValidationResult) -> None:
        """Validate a single asset entry against disk and hash.

        Args:
            entry: The AssetEntry to validate.
            result: The result accumulator to update.
        """
        if not self._check_file_exists(entry.relative_path):
            result.missing.append(entry.relative_path)
            return

        if entry.expected_hash is not None and not self._check_file_hash(
            entry.relative_path, entry.expected_hash
        ):
            result.corrupted.append(entry.relative_path)
            return

        result.valid.append(entry.relative_path)

    def get_required_assets(self) -> list[AssetEntry]:
        """Return the full list of assets required by the application.

        Returns:
            List of AssetEntry for fonts, templates, config, and migrations.
        """
        return (
            self._get_font_entries()
            + self._get_template_entries()
            + [AssetEntry(relative_path="app/config/defaults.json")]
            + self._get_migration_entries()
        )

    def get_asset_manifest(self) -> dict[str, str]:
        """Generate a manifest of all bundled assets and their SHA-256 hashes.

        Only includes assets that exist on disk.

        Returns:
            Dictionary mapping relative_path to SHA-256 hex digest.
        """
        manifest: dict[str, str] = {}
        for entry in self.get_required_assets():
            file_path = self.app_root / entry.relative_path
            if not file_path.is_file():
                continue
            try:
                sha256 = hashlib.sha256()
                with file_path.open("rb") as f:
                    for chunk in iter(lambda: f.read(65536), b""):
                        sha256.update(chunk)
                manifest[entry.relative_path] = sha256.hexdigest()
            except OSError:
                continue
        return manifest

    def _get_font_entries(self) -> list[AssetEntry]:
        """Build asset entries for bundled fonts.

        Returns:
            List of AssetEntry for font files.
        """
        font_dir = self.app_root / "assets" / "fonts"
        if not font_dir.is_dir():
            return []
        entries: list[AssetEntry] = []
        for f in sorted(font_dir.iterdir()):
            if f.suffix.lower() in (".ttf", ".otf"):
                relative = f"assets/fonts/{f.name}"
                entries.append(AssetEntry(relative_path=relative))
        return entries

    def _get_template_entries(self) -> list[AssetEntry]:
        """Build asset entries for bundled templates.

        Returns:
            List of AssetEntry for template files.
        """
        templates_dir = self.app_root / "assets" / "templates"
        if not templates_dir.is_dir():
            return []
        entries: list[AssetEntry] = []
        for f in sorted(templates_dir.iterdir()):
            if f.is_file():
                relative = f"assets/templates/{f.name}"
                entries.append(AssetEntry(relative_path=relative))
        return entries

    def _get_migration_entries(self) -> list[AssetEntry]:
        """Build asset entries for Alembic migration files.

        Returns:
            List of AssetEntry for migration files.
        """
        migrations_dir = self.app_root / "app" / "database" / "migrations"
        if not migrations_dir.is_dir():
            return []
        entries: list[AssetEntry] = []
        for f in sorted(migrations_dir.rglob("*.py")):
            if f.name == "__init__.py":
                continue
            relative = str(f.relative_to(self.app_root))
            entries.append(AssetEntry(relative_path=relative))
        return entries
