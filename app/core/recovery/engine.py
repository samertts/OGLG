from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from app.core.recovery.validator import WalRecoveryValidator


class RepairSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class RepairRecommendation:
    severity: RepairSeverity = RepairSeverity.INFO
    component: str = ""
    message: str = ""
    action: str = ""
    automated: bool = False


class RecoveryEngine:
    """Crash recovery launcher with repair recommendations."""

    def __init__(self, validator: WalRecoveryValidator) -> None:
        self._validator = validator
        self._recovery_attempts = 0

    def assess(self) -> dict[str, Any]:
        validation = self._validator.validate()
        recommendations = self._generate_recommendations(validation)
        return {
            "validation": validation,
            "recommendations": [
                {
                    "severity": r.severity.value,
                    "component": r.component,
                    "message": r.message,
                    "action": r.action,
                    "automated": r.automated,
                }
                for r in recommendations
            ],
            "recovery_attempts": self._recovery_attempts,
            "assessed_at": datetime.now(timezone.utc).isoformat(),
        }

    def _generate_recommendations(
        self, validation: dict[str, Any]
    ) -> list[RepairRecommendation]:
        recs: list[RepairRecommendation] = []
        if not validation.get("database_ok", True):
            recs.append(
                RepairRecommendation(
                    severity=RepairSeverity.CRITICAL,
                    component="database",
                    message=validation.get("database", {}).get(
                        "message", "Unknown database error"
                    ),
                    action="Run PRAGMA integrity_check and restore from latest backup",
                    automated=False,
                )
            )
        if not validation.get("wal_ok", True):
            recs.append(
                RepairRecommendation(
                    severity=RepairSeverity.WARNING,
                    component="wal",
                    message=validation.get("wal", {}).get(
                        "message", "Unknown WAL error"
                    ),
                    action="Delete WAL file and perform crash recovery",
                    automated=True,
                )
            )
        if not recs:
            recs.append(
                RepairRecommendation(
                    severity=RepairSeverity.INFO,
                    component="system",
                    message="System healthy — no recovery needed",
                    action="",
                    automated=True,
                )
            )
        return recs

    def attempt_recovery(self) -> dict[str, Any]:
        self._recovery_attempts += 1
        assessment = self.assess()
        return {
            "attempt": self._recovery_attempts,
            "status": "completed",
            "assessment": assessment,
            "message": "Recovery assessment completed — manual intervention may be needed",
        }
