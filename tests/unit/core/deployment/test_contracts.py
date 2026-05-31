from __future__ import annotations

from app.core.deployment.contracts import DeploymentConfig, DeploymentMode, DeploymentType


def test_deployment_config_defaults() -> None:
    cfg = DeploymentConfig()
    assert cfg.deployment_type == DeploymentType.PORTABLE
    assert cfg.mode == DeploymentMode.NORMAL
    assert cfg.app_name == "OGLG"


def test_deployment_config_is_portable() -> None:
    cfg = DeploymentConfig(deployment_type=DeploymentType.PORTABLE)
    assert cfg.is_portable()


def test_deployment_config_is_safe_mode() -> None:
    cfg = DeploymentConfig(mode=DeploymentMode.SAFE_MODE)
    assert cfg.is_safe_mode()


def test_deployment_config_to_dict() -> None:
    cfg = DeploymentConfig(app_version="2.0.0")
    d = cfg.to_dict()
    assert d["app_version"] == "2.0.0"
    assert d["deployment_type"] == "portable"
