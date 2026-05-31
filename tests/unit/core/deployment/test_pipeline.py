from __future__ import annotations

from pathlib import Path

from app.core.deployment.contracts import DeploymentConfig, DeploymentMode
from app.core.deployment.pipeline import StartupPipeline


def test_startup_pipeline_validates(tmp_path: Path) -> None:
    cfg = DeploymentConfig(
        data_dir=str(tmp_path / "data"),
        db_path=str(tmp_path / "db" / "app.db"),
        temp_dir=str(tmp_path / "temp"),
        log_dir=str(tmp_path / "logs"),
    )
    pipeline = StartupPipeline(cfg)
    result = pipeline.validate()
    assert result
    assert pipeline.all_passed
    assert len(pipeline.results) == 6


def test_startup_pipeline_failure_triggers_safe_mode(tmp_path: Path) -> None:
    cfg = DeploymentConfig(
        data_dir=str(tmp_path / "data"),
        db_path=str(tmp_path / "db" / "app.db"),
        temp_dir="/nonexistent_restricted_dir/sub",
        log_dir=str(tmp_path / "logs"),
        safe_mode_on_failure=True,
    )
    pipeline = StartupPipeline(cfg)
    result = pipeline.validate()
    assert not result
    assert pipeline._config.mode == DeploymentMode.SAFE_MODE


def test_startup_pipeline_summary(tmp_path: Path) -> None:
    cfg = DeploymentConfig(
        data_dir=str(tmp_path / "data"),
        db_path=str(tmp_path / "db" / "app.db"),
        temp_dir=str(tmp_path / "temp"),
        log_dir=str(tmp_path / "logs"),
    )
    pipeline = StartupPipeline(cfg)
    pipeline.validate()
    summary = pipeline.summary()
    assert "passed" in summary
    assert "mode" in summary
    assert "checks" in summary
    assert len(summary["checks"]) == 6
