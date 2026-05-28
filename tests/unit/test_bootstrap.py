"""Tests for the bootstrap container."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from app.bootstrap import build_container


class TestBuildContainer:
    def test_build_container_minimal(self, tmp_path: Path) -> None:
        container = build_container(
            data_dir_override=str(tmp_path),
            log_level="DEBUG",
        )
        assert container.settings is not None
        assert container.db_manager is not None
        assert container.letter_repo is not None
        assert container.user_repo is not None
        assert container.department_repo is not None
        assert container.attachment_repo is not None
        assert container.audit_repo is not None
        assert container.backup_repo is not None
        assert container.audit_service is not None
        assert container.backup_service is not None
        assert container.letter_service is not None
        assert container.data_dirs is not None
        container.close()

    def test_container_creates_data_dirs(self, tmp_path: Path) -> None:
        container = build_container(
            data_dir_override=str(tmp_path),
        )
        for name, path in container.data_dirs.items():
            assert path.is_dir(), f"{name} directory was not created"
        container.close()

    def test_container_close_disposes(self, tmp_path: Path) -> None:
        container = build_container(
            data_dir_override=str(tmp_path),
        )
        container.close()
