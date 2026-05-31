from __future__ import annotations

from pathlib import Path

from app.build.manifest import BuildManifest
from app.build.validator import BuildValidator, ValidationResult
from app.build.verifier import BuildVerifier


class TestBuildManifest:
    def test_create_manifest(self):
        m = BuildManifest(
            version="1.0.0",
            app_name="oglg",
            build_timestamp="2026-01-01T00:00:00",
            python_version="3.12",
        )
        m.add_entry("app/main.py", b"print('hello')")
        assert m.file_count == 1
        assert len(m.deterministic_id()) == 64

    def test_add_file(self, tmp_path: Path):
        f = tmp_path / "test.txt"
        f.write_text("data")
        m = BuildManifest(
            version="1.0.0", app_name="oglg",
            build_timestamp="now", python_version="3.12",
        )
        m.add_file(f, archive_prefix="app")
        assert m.file_count == 1
        assert m.entries[0].path == "app/test.txt"

    def test_json_roundtrip(self):
        m1 = BuildManifest(
            version="1.0.0", app_name="oglg",
            build_timestamp="now", python_version="3.12",
        )
        m1.add_entry("a.py", b"aaa")
        m1.add_entry("b.py", b"bbb")
        data = m1.to_json()
        m2 = BuildManifest.from_json(data)
        assert m2.version == m1.version
        assert m2.file_count == m1.file_count
        assert m2.deterministic_id() == m1.deterministic_id()

    def test_file_roundtrip(self, tmp_path: Path):
        m1 = BuildManifest(
            version="1.0.0", app_name="oglg",
            build_timestamp="now", python_version="3.12",
        )
        m1.add_entry("x.py", b"x")
        p = tmp_path / "manifest.json"
        m1.to_file(p)
        m2 = BuildManifest.from_file(p)
        assert m2.deterministic_id() == m1.deterministic_id()

    def test_deterministic_id_stable(self):
        m = BuildManifest(
            version="1.0.0", app_name="oglg",
            build_timestamp="now", python_version="3.12",
        )
        m.add_entry("a.py", b"content")
        assert m.deterministic_id() == m.deterministic_id()

    def test_total_size(self):
        m = BuildManifest(
            version="1.0.0", app_name="oglg",
            build_timestamp="now", python_version="3.12",
        )
        m.add_entry("a", b"12345")
        assert m.total_size_bytes == 5

    def test_empty_manifest(self):
        m = BuildManifest(
            version="1.0.0", app_name="oglg",
            build_timestamp="now", python_version="3.12",
        )
        assert m.file_count == 0
        assert m.total_size_bytes == 0


class TestBuildVerifier:
    def test_verify_artifact_match(self, tmp_path: Path):
        f = tmp_path / "artifact.bin"
        f.write_bytes(b"hello")
        m = BuildManifest(
            version="1.0.0", app_name="oglg",
            build_timestamp="now", python_version="3.12",
        )
        m.add_entry("artifact.bin", b"hello")
        v = BuildVerifier(m)
        assert v.verify_artifact(f, m.entries[0].sha256)

    def test_verify_artifact_mismatch(self, tmp_path: Path):
        f = tmp_path / "artifact.bin"
        f.write_bytes(b"hello")
        m = BuildManifest(
            version="1.0.0", app_name="oglg",
            build_timestamp="now", python_version="3.12",
        )
        m.add_entry("artifact.bin", b"world")
        v = BuildVerifier(m)
        assert not v.verify_artifact(f, m.entries[0].sha256)

    def test_verify_all_passes(self, tmp_path: Path):
        (tmp_path / "a.txt").write_text("aaa")
        (tmp_path / "b.txt").write_text("bbb")
        m = BuildManifest(
            version="1.0.0", app_name="oglg",
            build_timestamp="now", python_version="3.12",
        )
        m.add_entry("a.txt", b"aaa")
        m.add_entry("b.txt", b"bbb")
        v = BuildVerifier(m)
        r = v.verify_all(tmp_path)
        assert r.passed
        assert r.verified_count == 2

    def test_verify_all_missing(self, tmp_path: Path):
        m = BuildManifest(
            version="1.0.0", app_name="oglg",
            build_timestamp="now", python_version="3.12",
        )
        m.add_entry("missing.txt", b"data")
        v = BuildVerifier(m)
        r = v.verify_all(tmp_path)
        assert not r.passed
        assert len(r.missing) == 1

    def test_verify_all_mismatch(self, tmp_path: Path):
        (tmp_path / "a.txt").write_text("actual")
        m = BuildManifest(
            version="1.0.0", app_name="oglg",
            build_timestamp="now", python_version="3.12",
        )
        m.add_entry("a.txt", b"expected")
        v = BuildVerifier(m)
        r = v.verify_all(tmp_path)
        assert not r.passed
        assert len(r.mismatched) == 1

    def test_verify_all_detects_extra(self, tmp_path: Path):
        (tmp_path / "extra.txt").write_text("extra")
        m = BuildManifest(
            version="1.0.0", app_name="oglg",
            build_timestamp="now", python_version="3.12",
        )
        v = BuildVerifier(m)
        r = v.verify_all(tmp_path)
        assert len(r.extra) == 1

    def test_release_integrity_with_list(self, tmp_path: Path):
        a = tmp_path / "release.zip"
        a.write_text("zip data")
        b = tmp_path / "release.sig"
        b.write_text("sig data")
        m = BuildManifest(
            version="1.0.0", app_name="oglg",
            build_timestamp="now", python_version="3.12",
        )
        m.add_entry("release.zip", b"zip data")
        m.add_entry("release.sig", b"sig data")
        v = BuildVerifier(m)
        r = v.verify_release_integrity([a, b])
        assert r.passed
        assert r.verified_count == 2


class TestBuildValidator:
    def test_environment_validation(self):
        v = BuildValidator()
        r = v.validate_environment()
        assert isinstance(r, ValidationResult)
        assert "python_version" in r.checks
        assert "sqlite_version" in r.checks

    def test_manifest_determinism(self):
        m = BuildManifest(
            version="1.0.0", app_name="oglg",
            build_timestamp="now", python_version="3.12",
        )
        m.add_entry("a.txt", b"content")
        v = BuildValidator()
        sources = [Path("a.txt")]
        r = v.validate_manifest_determinism(sources, m)
        assert r.passed

    def test_rollback_safe_validation(self, tmp_path: Path):
        m = BuildManifest(
            version="1.0.0", app_name="oglg",
            build_timestamp="now", python_version="3.12",
        )
        m.add_entry("test.py", b"code")
        p = tmp_path / "manifest.json"
        m.to_file(p)
        v = BuildValidator()
        r = v.validate_rollback_safe(p)
        assert r.passed

    def test_rollback_safe_missing(self):
        v = BuildValidator()
        r = v.validate_rollback_safe(Path("/nonexistent/manifest.json"))
        assert not r.passed
