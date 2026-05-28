"""Tests for settings loading."""

import json
from pathlib import Path

import pytest

from app.config.settings import Settings, load_defaults, load_settings


class TestSettings:
    def test_default_creation(self) -> None:
        settings = Settings()
        assert settings.app_name == "OGLG"
        assert settings.log_level == "INFO"
        assert settings.auto_backup_enabled
        assert settings.search_page_size == 50

    def test_from_dict(self) -> None:
        data = {
            "log_level": "DEBUG",
            "auto_backup_enabled": False,
            "search_page_size": 100,
        }
        settings = Settings.from_dict(data)
        assert settings.log_level == "DEBUG"
        assert not settings.auto_backup_enabled
        assert settings.search_page_size == 100

    def test_from_dict_ignores_invalid_keys(self) -> None:
        data = {
            "log_level": "WARNING",
            "nonexistent_key": "value",
        }
        settings = Settings.from_dict(data)
        assert settings.log_level == "WARNING"
        assert not hasattr(settings, "nonexistent_key")

    def test_to_dict(self) -> None:
        settings = Settings(log_level="ERROR")
        d = settings.to_dict()
        assert d["log_level"] == "ERROR"
        assert d["app_name"] == "OGLG"
        assert "data_dir" in d


class TestLoadDefaults:
    def test_load_defaults_from_file(self, tmp_path: Path) -> None:
        defaults = tmp_path / "defaults.json"
        defaults.write_text(
            json.dumps({"log_level": "WARNING", "search_page_size": 200}),
            encoding="utf-8",
        )
        settings = load_defaults(defaults)
        assert settings.log_level == "WARNING"
        assert settings.search_page_size == 200

    def test_load_defaults_missing_file(self, tmp_path: Path) -> None:
        settings = load_defaults(tmp_path / "nonexistent.json")
        assert isinstance(settings, Settings)
        assert settings.log_level == "INFO"


class TestLoadSettings:
    def test_load_settings_with_defaults(self, tmp_path: Path) -> None:
        defaults = tmp_path / "defaults.json"
        defaults.write_text(
            json.dumps({"log_level": "DEBUG"}),
            encoding="utf-8",
        )
        settings = load_settings(
            defaults_path=defaults,
            data_dir=tmp_path,
        )
        assert settings.log_level == "DEBUG"
        assert settings.data_dir == tmp_path

    def test_load_settings_with_user_override(self, tmp_path: Path) -> None:
        defaults = tmp_path / "defaults.json"
        defaults.write_text(
            json.dumps({"log_level": "DEBUG"}),
            encoding="utf-8",
        )
        user_config = tmp_path / "user_config.json"
        user_config.write_text(
            json.dumps({"log_level": "ERROR"}),
            encoding="utf-8",
        )
        settings = load_settings(
            defaults_path=defaults,
            user_config_path=user_config,
            data_dir=tmp_path,
        )
        assert settings.log_level == "ERROR"

    def test_load_settings_sets_paths(self, tmp_path: Path) -> None:
        defaults = tmp_path / "defaults.json"
        defaults.write_text("{}", encoding="utf-8")
        settings = load_settings(
            defaults_path=defaults,
            data_dir=tmp_path,
        )
        assert settings.database_path == tmp_path / "database" / "correspondence.db"
        assert settings.archive_path == tmp_path / "archives"
        assert settings.backup_path == tmp_path / "backups"
        assert settings.log_path == tmp_path / "logs"
        assert settings.temp_path == tmp_path / "temp"

    def test_save_user_config(self, tmp_path: Path) -> None:
        settings = Settings(log_level="DEBUG", language="EN")
        config_path = tmp_path / "user_config.json"
        settings.save_user_config(config_path)
        assert config_path.exists()
        data = json.loads(config_path.read_text(encoding="utf-8"))
        assert data["log_level"] == "DEBUG"
        assert data["language"] == "EN"
