from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class DeploymentType(Enum):
    PORTABLE = "portable"
    INSTALLED = "installed"


class DeploymentMode(Enum):
    NORMAL = "normal"
    SAFE_MODE = "safe_mode"
    RECOVERY = "recovery"
    READ_ONLY = "read_only"


@dataclass
class DeploymentConfig:
    deployment_type: DeploymentType = DeploymentType.PORTABLE
    mode: DeploymentMode = DeploymentMode.NORMAL
    app_name: str = "OGLG"
    app_version: str = "1.0.0"
    data_dir: str = ""
    db_path: str = ""
    temp_dir: str = ""
    log_dir: str = ""
    max_startup_retries: int = 3
    safe_mode_on_failure: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def is_portable(self) -> bool:
        return self.deployment_type == DeploymentType.PORTABLE

    def is_safe_mode(self) -> bool:
        return self.mode == DeploymentMode.SAFE_MODE

    def to_dict(self) -> dict[str, Any]:
        return {
            "deployment_type": self.deployment_type.value,
            "mode": self.mode.value,
            "app_name": self.app_name,
            "app_version": self.app_version,
            "data_dir": self.data_dir,
            "db_path": self.db_path,
            "temp_dir": self.temp_dir,
            "log_dir": self.log_dir,
            "max_startup_retries": self.max_startup_retries,
            "safe_mode_on_failure": self.safe_mode_on_failure,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
        }
