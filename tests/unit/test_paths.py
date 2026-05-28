"""Tests for path management utilities."""

import sys
from pathlib import Path

import pytest

from app.utils.paths import (
    ensure_data_directories,
    get_config_path,
    get_database_path,
    get_default_config_path,
    get_log_dir,
    get_migrations_dir,
    is_portable_mode,
    resolve_data_directory,
    resolve_project_root,
)


class TestResolveProjectRoot:
    def test_resolve_project_root(self) -> None:
        root = resolve_project_root()
        assert root.is_dir()
        assert (root / "app").is_dir()

    def test_returns_absolute_path(self) -> None:
        root = resolve_project_root()
        assert root.is_absolute()


class TestResolveDataDirectory:
    def test_portable_data_dir(self, tmp_path: Path) -> None:
        data_dir = resolve_data_directory(portable=True)
        assert "data" in str(data_dir)

    def test_installed_data_dir(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            "app.utils.paths.platform.system", lambda: "Linux"
        )
        monkeypatch.setattr("pathlib.Path.home", lambda: Path("/home/user"))
        data_dir = resolve_data_directory(portable=False)
        assert str(data_dir) == "/home/user/.local/share/oglg"


class TestEnsureDataDirectories:
    def test_creates_all_dirs(self, tmp_path: Path) -> None:
        dirs = ensure_data_directories(tmp_path)
        expected = [
            "database",
            "archives",
            "backups",
            "generated_letters",
            "attachments",
            "logs",
            "temp",
        ]
        for key in expected:
            assert key in dirs
            assert dirs[key].is_dir()

    def test_returns_dict(self, tmp_path: Path) -> None:
        dirs = ensure_data_directories(tmp_path)
        assert isinstance(dirs, dict)
        assert len(dirs) == 7


class TestGetDatabasePath:
    def test_returns_correct_path(self, tmp_path: Path) -> None:
        path = get_database_path(tmp_path)
        assert path == tmp_path / "database" / "correspondence.db"
        assert path.suffix == ".db"


class TestGetConfigPath:
    def test_returns_correct_path(self, tmp_path: Path) -> None:
        path = get_config_path(tmp_path)
        assert path == tmp_path / "user_config.json"
        assert path.suffix == ".json"


class TestGetDefaultConfigPath:
    def test_returns_existing_file(self) -> None:
        path = get_default_config_path()
        assert path.exists()
        assert path.name == "defaults.json"


class TestGetMigrationsDir:
    def test_returns_existing_dir(self) -> None:
        path = get_migrations_dir()
        assert path.is_dir()
        assert "migrations" in str(path)


class TestGetLogDir:
    def test_returns_log_dir(self, tmp_path: Path) -> None:
        path = get_log_dir(tmp_path)
        assert path == tmp_path / "logs"


class TestIsPortableMode:
    def test_no_portable_marker(self) -> None:
        assert not is_portable_mode()

    def test_with_portable_marker(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            "app.utils.paths.resolve_project_root",
            lambda: Path("/tmp/mock_root"),
        )
        assert not is_portable_mode()
