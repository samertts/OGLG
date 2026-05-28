"""Tests for file utility functions."""

from pathlib import Path

import pytest

from app.utils.file_utils import (
    atomic_write,
    atomic_write_stream,
    atomic_move,
    cleanup_temp_files,
    compute_data_hash,
    compute_file_hash,
    create_temp_file,
    ensure_directory,
    get_disk_usage,
    safe_remove,
)


class TestAtomicWrite:
    def test_atomic_write_creates_file(self, tmp_path: Path) -> None:
        target = tmp_path / "test.txt"
        result = atomic_write(target, b"hello world")
        assert result == target.resolve()
        assert target.read_bytes() == b"hello world"

    def test_atomic_write_overwrites(self, tmp_path: Path) -> None:
        target = tmp_path / "test.txt"
        target.write_bytes(b"original")
        atomic_write(target, b"modified")
        assert target.read_bytes() == b"modified"

    def test_atomic_write_creates_parent_dirs(self, tmp_path: Path) -> None:
        target = tmp_path / "nested" / "deep" / "test.txt"
        atomic_write(target, b"content")
        assert target.exists()

    def test_atomic_write_no_temp_leftover(self, tmp_path: Path) -> None:
        target = tmp_path / "test.txt"
        atomic_write(target, b"content")
        temp_files = list(tmp_path.glob("*.tmp"))
        assert len(temp_files) == 0


class TestAtomicWriteStream:
    def test_atomic_write_stream(self, tmp_path: Path) -> None:
        target = tmp_path / "test.bin"
        import io
        stream = io.BytesIO(b"stream data")
        result = atomic_write_stream(target, stream)
        assert result == target.resolve()
        assert target.read_bytes() == b"stream data"


class TestAtomicMove:
    def test_atomic_move(self, tmp_path: Path) -> None:
        src = tmp_path / "source.txt"
        dst = tmp_path / "dest.txt"
        src.write_bytes(b"movable")
        result = atomic_move(src, dst)
        assert result == dst.resolve()
        assert dst.read_bytes() == b"movable"
        assert not src.exists()

    def test_atomic_move_creates_parent(self, tmp_path: Path) -> None:
        src = tmp_path / "source.txt"
        dst = tmp_path / "subdir" / "dest.txt"
        src.write_bytes(b"movable")
        atomic_move(src, dst)
        assert dst.exists()


class TestComputeHash:
    def test_compute_data_hash(self) -> None:
        h = compute_data_hash(b"hello")
        assert len(h) == 64
        assert h == "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"

    def test_compute_file_hash(self, tmp_path: Path) -> None:
        f = tmp_path / "data.bin"
        f.write_bytes(b"file content")
        h = compute_file_hash(f)
        assert len(h) == 64

    def test_compute_hash_empty(self) -> None:
        h = compute_data_hash(b"")
        assert h == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"


class TestEnsureDirectory:
    def test_ensure_directory_creates(self, tmp_path: Path) -> None:
        d = tmp_path / "new_dir"
        result = ensure_directory(d)
        assert result == d
        assert d.is_dir()

    def test_ensure_directory_exists(self, tmp_path: Path) -> None:
        d = tmp_path / "existing"
        d.mkdir()
        result = ensure_directory(d)
        assert result == d

    def test_ensure_nested(self, tmp_path: Path) -> None:
        d = tmp_path / "a" / "b" / "c"
        ensure_directory(d)
        assert d.is_dir()


class TestSafeRemove:
    def test_safe_remove_file(self, tmp_path: Path) -> None:
        f = tmp_path / "delete_me.txt"
        f.write_bytes(b"bye")
        assert safe_remove(f)
        assert not f.exists()

    def test_safe_remove_nonexistent(self, tmp_path: Path) -> None:
        assert not safe_remove(tmp_path / "ghost.txt")

    def test_safe_remove_directory_fails(self, tmp_path: Path) -> None:
        d = tmp_path / "a_dir"
        d.mkdir()
        assert not safe_remove(d)


class TestCleanupTempFiles:
    def test_cleanup_none(self, tmp_path: Path) -> None:
        assert cleanup_temp_files(tmp_path) == 0

    def test_cleanup_old_temp(self, tmp_path: Path) -> None:
        old = tmp_path / "old.tmp"
        old.write_bytes(b"old")
        import time
        time.sleep(0.01)
        assert cleanup_temp_files(tmp_path, max_age_hours=0) >= 1
        assert not old.exists()

    def test_cleanup_recent_kept(self, tmp_path: Path) -> None:
        recent = tmp_path / "recent.tmp"
        recent.write_bytes(b"new")
        assert cleanup_temp_files(tmp_path, max_age_hours=24) == 0
        assert recent.exists()


class TestCreateTempFile:
    def test_create_temp_file(self) -> None:
        path, name = create_temp_file()
        assert path.exists()
        assert name.endswith(".tmp")
        path.unlink()

    def test_create_temp_with_suffix(self) -> None:
        path, name = create_temp_file(suffix=".test")
        assert name.endswith(".test")
        path.unlink()


class TestGetDiskUsage:
    def test_get_disk_usage(self, tmp_path: Path) -> None:
        total, used, free = get_disk_usage(tmp_path)
        assert total > 0
        assert used >= 0
        assert free >= 0
