from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any


@dataclass
class Settings:
    """Application configuration loaded from defaults + user overrides.

    Loading order (later overrides earlier):
        1. defaults.json (bundled with application)
        2. user_config.json (in user data directory)
        3. Database system_config table (runtime overrides)
        4. CLI arguments (session overrides)
    """

    # Paths
    data_dir: Path = Path("")
    database_path: Path = Path("")
    archive_path: Path = Path("")
    backup_path: Path = Path("")
    log_path: Path = Path("")
    temp_path: Path = Path("")
    attachment_path: Path = Path("")
    generated_letters_path: Path = Path("")

    # Database
    db_pool_size: int = 1
    db_timeout: int = 5
    db_wal_mode: bool = True

    # Logging
    log_level: str = "INFO"
    log_rotation: str = "10 MB"
    log_retention: str = "30 days"
    log_json_format: bool = False

    # Backup
    auto_backup_enabled: bool = True
    auto_backup_interval_days: int = 1
    backup_retention_days: int = 30

    # PDF
    pdf_dpi: int = 300
    pdf_default_template: str = "official_letter"

    # AI
    ai_enabled: bool = True
    ai_language: str = "AR"

    # Security
    password_min_length: int = 8
    session_timeout_minutes: int = 30
    max_login_attempts: int = 5

    # Performance
    search_page_size: int = 50
    archive_page_size: int = 50

    # System
    app_name: str = "OGLG"
    app_version: str = "1.0.0"
    app_org: str = "Iraq Ministry of Health"
    language: str = "AR"
    theme: str = "default"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Settings:
        valid_fields = {f.name for f in dataclass_fields(cls)}
        filtered = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered)

    def save_user_config(self, path: Path) -> None:
        """Save only user-configurable settings to a JSON file."""
        user_config = {
            "log_level": self.log_level,
            "auto_backup_enabled": self.auto_backup_enabled,
            "auto_backup_interval_days": self.auto_backup_interval_days,
            "backup_retention_days": self.backup_retention_days,
            "log_json_format": self.log_json_format,
            "language": self.language,
            "theme": self.theme,
            "ai_enabled": self.ai_enabled,
            "ai_language": self.ai_language,
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(user_config, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )


def dataclass_fields(cls: type) -> list:
    import dataclasses
    return dataclasses.fields(cls)


def load_settings(
    defaults_path: Path,
    user_config_path: Path | None = None,
    data_dir: Path | None = None,
) -> Settings:
    """Load settings from defaults and optional user config.

    Args:
        defaults_path: Path to bundled defaults.json.
        user_config_path: Optional path to user configuration file.
        data_dir: Optional data directory override (from CLI or portable mode).

    Returns:
        Fully initialized Settings instance.
    """
    base = load_defaults(defaults_path)

    if user_config_path and user_config_path.exists():
        user_overrides = json.loads(user_config_path.read_text(encoding="utf-8"))
        for k, v in user_overrides.items():
            if hasattr(base, k):
                setattr(base, k, v)

    resolved_data_dir = data_dir or Path("")
    base.data_dir = resolved_data_dir
    base.database_path = resolved_data_dir / "database" / "correspondence.db"
    base.archive_path = resolved_data_dir / "archives"
    base.backup_path = resolved_data_dir / "backups"
    base.log_path = resolved_data_dir / "logs"
    base.temp_path = resolved_data_dir / "temp"
    base.attachment_path = resolved_data_dir / "attachments"
    base.generated_letters_path = resolved_data_dir / "generated_letters"

    return base


def load_defaults(path: Path) -> Settings:
    """Load default settings from the bundled defaults.json.

    Args:
        path: Path to defaults.json.

    Returns:
        Settings instance with defaults applied.
    """
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        return Settings.from_dict(data)
    return Settings()
