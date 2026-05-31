from __future__ import annotations

import json
import sqlite3
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass
class DeploymentHealthReport:
    timestamp: str
    db_integrity: bool
    wal_healthy: bool
    disk_free_bytes: int
    component_count: int
    healthy_count: int
    detail: str


@dataclass
class ReplayIntegrityReport:
    event_count: int
    sequence_continuous: bool
    first_id: int
    last_id: int
    detail: str


@dataclass
class WalSurvivabilityReport:
    wal_exists: bool
    wal_valid: bool
    wal_size_bytes: int
    checkpoint_sequence: int
    detail: str


@dataclass
class ArchiveHealthSummary:
    snapshot_count: int
    attachment_count: int
    total_size_bytes: int
    integrity_pass: int
    integrity_fail: int
    detail: str


@dataclass
class FederationContinuitySummary:
    identity_count: int
    protocol_version: str
    sync_window_hours: float
    detail: str


@dataclass
class RbacValidationReport:
    role_count: int
    permission_count: int
    assignment_count: int
    detail: str


@dataclass
class DiagnosticSummary:
    deployment: DeploymentHealthReport | None = None
    replay: ReplayIntegrityReport | None = None
    wal: WalSurvivabilityReport | None = None
    archive: ArchiveHealthSummary | None = None
    federation: FederationContinuitySummary | None = None
    rbac: RbacValidationReport | None = None
    duration_seconds: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        raw = asdict(self)
        result: dict[str, Any] = {}
        for k, v in raw.items():
            if isinstance(v, dict):
                result[k] = {
                    sk: sv for sk, sv in v.items()
                    if not sk.startswith("_")
                }
            else:
                result[k] = v
        return result

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True)


class GovernanceReporter:
    def __init__(self, db_path: Path | None = None) -> None:
        self._db_path = db_path

    def _connect(self) -> sqlite3.Connection:
        if self._db_path is None or not self._db_path.exists():
            raise FileNotFoundError(f"Database not found: {self._db_path}")
        conn = sqlite3.connect(str(self._db_path))
        conn.execute("PRAGMA journal_mode=WAL")
        conn.row_factory = sqlite3.Row
        return conn

    def _fmt_time(self) -> str:
        import datetime
        return datetime.datetime.now(datetime.timezone.utc).isoformat()

    # -- deployment health --

    def deployment_health(self) -> DeploymentHealthReport:
        if self._db_path is None:
            return DeploymentHealthReport(
                timestamp=self._fmt_time(),
                db_integrity=False,
                wal_healthy=False,
                disk_free_bytes=0,
                component_count=0,
                healthy_count=0,
                detail="no db_path configured",
            )
        integrity = False
        wal_ok = False
        try:
            conn = self._connect()
            row = conn.execute("PRAGMA integrity_check").fetchone()
            integrity = row is not None and row[0] == "ok"

            wal_path = self._db_path.with_suffix(self._db_path.suffix + "-wal")
            if wal_path.exists():
                with open(wal_path, "rb") as f:
                    magic = f.read(16)
                    wal_ok = magic == b"SQLite format 3\x00"
            else:
                wal_ok = True

            conn.close()
        except Exception:
            pass

        return DeploymentHealthReport(
            timestamp=self._fmt_time(),
            db_integrity=integrity,
            wal_healthy=wal_ok,
            disk_free_bytes=0,
            component_count=3,
            healthy_count=sum([integrity, wal_ok]),
            detail=f"integrity={'ok' if integrity else 'fail'}, wal={'ok' if wal_ok else 'fail'}",
        )

    # -- replay integrity --

    def replay_integrity(self, event_store_path: Path) -> ReplayIntegrityReport:
        try:
            conn = sqlite3.connect(str(event_store_path))
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT MIN(id) as min_id, MAX(id) as max_id, "
                "COUNT(*) as cnt FROM events"
            ).fetchone()
            conn.close()

            if rows is None:
                return ReplayIntegrityReport(
                    event_count=0, sequence_continuous=True,
                    first_id=0, last_id=0, detail="empty event store",
                )

            cnt = rows["cnt"]
            first_id = rows["min_id"]
            last_id = rows["max_id"]
            continuous = (last_id - first_id + 1) == cnt if cnt > 0 else True

            return ReplayIntegrityReport(
                event_count=cnt,
                sequence_continuous=continuous,
                first_id=first_id,
                last_id=last_id,
                detail=f"{cnt} events, ids {first_id}-{last_id}, "
                f"{'continuous' if continuous else 'gap detected'}",
            )
        except Exception as e:
            return ReplayIntegrityReport(
                event_count=0, sequence_continuous=False,
                first_id=0, last_id=0, detail=str(e),
            )

    # -- WAL survivability --

    def wal_survivability(self) -> WalSurvivabilityReport:
        if self._db_path is None:
            return WalSurvivabilityReport(
                wal_exists=False, wal_valid=False,
                wal_size_bytes=0, checkpoint_sequence=0,
                detail="no db_path",
            )
        wal_path = self._db_path.with_suffix(self._db_path.suffix + "-wal")
        if not wal_path.exists():
            return WalSurvivabilityReport(
                wal_exists=False, wal_valid=True,
                wal_size_bytes=0, checkpoint_sequence=0,
                detail="no WAL file (not in WAL mode)",
            )
        try:
            with open(wal_path, "rb") as f:
                header = f.read(36)
                magic = header[:16]
                valid = magic == b"SQLite format 3\x00"
                import struct
                ckpt_seq = struct.unpack(">I", header[24:28])[0]
                size = wal_path.stat().st_size
            return WalSurvivabilityReport(
                wal_exists=True,
                wal_valid=valid,
                wal_size_bytes=size,
                checkpoint_sequence=ckpt_seq,
                detail=f"WAL {'valid' if valid else 'invalid'}, "
                f"size={size}, ckpt_seq={ckpt_seq}",
            )
        except Exception as e:
            return WalSurvivabilityReport(
                wal_exists=True, wal_valid=False,
                wal_size_bytes=0, checkpoint_sequence=0,
                detail=str(e),
            )

    # -- archive health --

    def archive_health(self, archive_db: Path) -> ArchiveHealthSummary:
        try:
            conn = sqlite3.connect(str(archive_db))
            conn.row_factory = sqlite3.Row

            snap_count = conn.execute(
                "SELECT COUNT(*) as c FROM archive_index"
            ).fetchone()["c"]

            attach_count = conn.execute(
                "SELECT COUNT(*) as c FROM archive_attachment"
            ).fetchone()["c"]

            size = archive_db.stat().st_size if archive_db.exists() else 0

            total = 0
            passed = 0
            for row in conn.execute(
                "SELECT snapshot_id, checksum, data FROM archive_index"
            ).fetchall():
                total += 1
                import hashlib
                import json
                data = json.loads(row["data"])
                snap_checksum = hashlib.sha256(
                    json.dumps(data, sort_keys=True).encode()
                ).hexdigest()
                if snap_checksum == row["checksum"]:
                    passed += 1

            conn.close()

            return ArchiveHealthSummary(
                snapshot_count=snap_count,
                attachment_count=attach_count,
                total_size_bytes=size,
                integrity_pass=passed,
                integrity_fail=total - passed,
                detail=f"{passed}/{total} snapshots valid, "
                f"{attach_count} attachments",
            )
        except Exception as e:
            return ArchiveHealthSummary(
                snapshot_count=0, attachment_count=0,
                total_size_bytes=0, integrity_pass=0,
                integrity_fail=0, detail=str(e),
            )

    # -- federation continuity --

    def federation_continuity(self) -> FederationContinuitySummary:
        try:
            conn = self._connect()
            identities = conn.execute(
                "SELECT COUNT(*) as c FROM federation_identity"
            ).fetchone()["c"] if self._has_table("federation_identity") else 0
            conn.close()
        except Exception:
            identities = 0

        return FederationContinuitySummary(
            identity_count=identities,
            protocol_version="1.0",
            sync_window_hours=72.0,
            detail=f"{identities} federated identities, protocol 1.0",
        )

    def _has_table(self, name: str) -> bool:
        if self._db_path is None:
            return False
        try:
            conn = self._connect()
            row = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (name,),
            ).fetchone()
            conn.close()
            return row is not None
        except Exception:
            return False

    # -- RBAC validation --

    def rbac_validation(self) -> RbacValidationReport:
        try:
            conn = self._connect()
            roles = conn.execute(
                "SELECT COUNT(*) as c FROM roles"
            ).fetchone()["c"] if self._has_table("roles") else 0

            permissions = conn.execute(
                "SELECT COUNT(*) as c FROM permissions"
            ).fetchone()["c"] if self._has_table("permissions") else 0

            assignments = conn.execute(
                "SELECT COUNT(*) as c FROM role_assignments"
            ).fetchone()["c"] if self._has_table("role_assignments") else 0

            conn.close()
        except Exception:
            roles = 0
            permissions = 0
            assignments = 0

        return RbacValidationReport(
            role_count=roles,
            permission_count=permissions,
            assignment_count=assignments,
            detail=f"{roles} roles, {permissions} permissions, "
            f"{assignments} assignments",
        )

    # -- diagnostic summary --

    def full_diagnostic(
        self,
        event_store_path: Path | None = None,
        archive_db_path: Path | None = None,
    ) -> DiagnosticSummary:
        start = time.monotonic()
        dep = self.deployment_health()
        wal = self.wal_survivability()
        replay = (
            self.replay_integrity(event_store_path)
            if event_store_path is not None
            else None
        )
        archive = (
            self.archive_health(archive_db_path)
            if archive_db_path is not None
            else None
        )
        fed = self.federation_continuity()
        rbac = self.rbac_validation()
        return DiagnosticSummary(
            deployment=dep,
            replay=replay,
            wal=wal,
            archive=archive,
            federation=fed,
            rbac=rbac,
            duration_seconds=time.monotonic() - start,
        )
