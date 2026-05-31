from __future__ import annotations

import json
import sqlite3
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ForensicsReport:
    scenario: str
    passed: bool
    duration_seconds: float = 0.0
    detail: str = ""
    entry_count: int = 0
    bundle_size_bytes: int = 0
    data: dict[str, Any] = field(default_factory=dict)


class ForensicsEngine:
    def __init__(self, workspace: Path) -> None:
        self._workspace = workspace
        self._workspace.mkdir(parents=True, exist_ok=True)
        self._diagnostics: dict[str, Any] = {}
        self._timeline: list[dict[str, Any]] = []

    def capture_runtime_diagnostics(self) -> ForensicsReport:
        start = time.monotonic()
        import sys
        self._diagnostics = {
            "python_version": (
                f"{sys.version_info.major}."
                f"{sys.version_info.minor}."
                f"{sys.version_info.micro}"
            ),
            "platform": sys.platform,
            "timestamp": time.monotonic(),
            "diagnostics_count": 0,
        }
        return ForensicsReport(
            "runtime_diagnostics", True, time.monotonic() - start,
            "diagnostics captured", data=dict(self._diagnostics),
        )

    def capture_audit_snapshot(self, db_path: Path) -> ForensicsReport:
        start = time.monotonic()
        try:
            conn = sqlite3.connect(str(db_path), timeout=5.0)
            tables = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
            snapshot: dict[str, Any] = {"tables": {}, "wal_mode": False}
            for (tname,) in tables:
                count = conn.execute(
                    f"SELECT COUNT(*) FROM \"{tname}\""
                ).fetchone()[0]
                snapshot["tables"][tname] = count
            journal = conn.execute(
                "PRAGMA journal_mode"
            ).fetchone()
            snapshot["wal_mode"] = journal and journal[0] == "wal"
            conn.close()
            return ForensicsReport(
                "audit_snapshot", True, time.monotonic() - start,
                f"tables={len(snapshot['tables'])}, rows={sum(snapshot['tables'].values())}",
                entry_count=sum(snapshot["tables"].values()),
                data=snapshot,
            )
        except Exception as e:
            return ForensicsReport("audit_snapshot", False, time.monotonic() - start, str(e))

    def capture_replay_metadata(self, db_path: Path) -> ForensicsReport:
        start = time.monotonic()
        try:
            conn = sqlite3.connect(str(db_path), timeout=5.0)
            wal_mode = conn.execute("PRAGMA journal_mode").fetchone()
            integrity = conn.execute("PRAGMA integrity_check").fetchone()
            page_count = conn.execute("PRAGMA page_count").fetchone()
            page_size = conn.execute("PRAGMA page_size").fetchone()
            conn.close()
            meta = {
                "wal": wal_mode[0] if wal_mode else None,
                "integrity": integrity[0] if integrity else None,
                "pages": page_count[0] if page_count else 0,
                "page_size": page_size[0] if page_size else 0,
            }
            return ForensicsReport(
                "replay_metadata", True, time.monotonic() - start,
                f"wal={meta['wal']}, integrity={meta['integrity']}, pages={meta['pages']}",
                data=meta,
            )
        except Exception as e:
            return ForensicsReport("replay_metadata", False, time.monotonic() - start, str(e))

    def record_operator_action(self, operator: str, action: str, detail: str = "") -> None:
        self._timeline.append({
            "timestamp": time.monotonic(),
            "operator": operator,
            "action": action,
            "detail": detail,
        })

    def export_operator_timeline(self) -> ForensicsReport:
        start = time.monotonic()
        count = len(self._timeline)
        return ForensicsReport(
            "operator_timeline", True, time.monotonic() - start,
            f"actions={count}", entry_count=count,
            data={"entries": list(self._timeline)},
        )

    def capture_crash_reconstruction(self, db_path: Path) -> ForensicsReport:
        start = time.monotonic()
        try:
            conn = sqlite3.connect(str(db_path), timeout=5.0)
            wal = conn.execute("PRAGMA wal_checkpoint").fetchone()
            integrity = conn.execute("PRAGMA integrity_check").fetchone()
            journal = conn.execute("PRAGMA journal_mode").fetchone()
            conn.close()
            data = {
                "wal_checkpoint": list(wal) if wal else [],
                "integrity": integrity[0] if integrity else "unknown",
                "journal_mode": journal[0] if journal else "unknown",
            }
            ok = integrity is not None and integrity[0] == "ok"
            return ForensicsReport(
                "crash_reconstruction", ok, time.monotonic() - start,
                f"integrity={data['integrity']}, journal={data['journal_mode']}",
                data=data,
            )
        except Exception as e:
            return ForensicsReport("crash_reconstruction", False, time.monotonic() - start, str(e))

    def diagnose_wal_incident(self, db_path: Path) -> ForensicsReport:
        start = time.monotonic()
        try:
            conn = sqlite3.connect(str(db_path), timeout=5.0)
            journal = conn.execute("PRAGMA journal_mode").fetchone()
            wal_status = conn.execute("PRAGMA wal_checkpoint").fetchone()
            integrity = conn.execute("PRAGMA integrity_check").fetchone()
            conn.close()
            data = {
                "journal": journal[0] if journal else "unknown",
                "wal_status": list(wal_status) if wal_status else [],
                "integrity": integrity[0] if integrity else "unknown",
            }
            ok = integrity is not None and integrity[0] == "ok"
            return ForensicsReport(
                "wal_incident", ok, time.monotonic() - start,
                f"journal={data['journal']}, integrity={data['integrity']}",
                data=data,
            )
        except Exception as e:
            return ForensicsReport("wal_incident", False, time.monotonic() - start, str(e))

    def diagnose_sync_incident(self, db_path: Path) -> ForensicsReport:
        start = time.monotonic()
        try:
            conn = sqlite3.connect(str(db_path), timeout=5.0)
            tables = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
            sync_tables = {}
            for (tname,) in tables:
                if "sync" in tname.lower() or "queue" in tname.lower():
                    cnt = conn.execute(f"SELECT COUNT(*) FROM \"{tname}\"").fetchone()[0]
                    sync_tables[tname] = cnt
            conn.close()
            return ForensicsReport(
                "sync_incident", True, time.monotonic() - start,
                f"sync_tables={len(sync_tables)}",
                entry_count=sum(sync_tables.values()),
                data=sync_tables,
            )
        except Exception as e:
            return ForensicsReport("sync_incident", False, time.monotonic() - start, str(e))

    def trace_queue_replay(self, db_path: Path) -> ForensicsReport:
        start = time.monotonic()
        try:
            conn = sqlite3.connect(str(db_path), timeout=5.0)
            tables = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
            queue_tables = {}
            for (tname,) in tables:
                if "queue" in tname.lower():
                    cnt = conn.execute(f"SELECT COUNT(*) FROM \"{tname}\"").fetchone()[0]
                    queue_tables[tname] = cnt
            conn.close()
            return ForensicsReport(
                "queue_replay_trace", True, time.monotonic() - start,
                f"queue_tables={len(queue_tables)}",
                entry_count=sum(queue_tables.values()),
                data=queue_tables,
            )
        except Exception as e:
            return ForensicsReport("queue_replay_trace", False, time.monotonic() - start, str(e))

    def export_incident_bundle(self, db_path: Path) -> ForensicsReport:
        start = time.monotonic()
        bundle: dict[str, Any] = {}
        try:
            conn = sqlite3.connect(str(db_path), timeout=5.0)
            for (tname,) in conn.execute("SELECT name FROM sqlite_master WHERE type='table'"):
                rows = conn.execute(f"SELECT * FROM \"{tname}\" LIMIT 100").fetchall()
                bundle[tname] = [list(r) for r in rows]
            conn.close()
            export_path = self._workspace / f"incident_bundle_{int(time.time())}.json"
            raw = json.dumps(bundle, default=str)
            export_path.write_text(raw)
            size = len(raw)
            return ForensicsReport(
                "incident_bundle", True, time.monotonic() - start,
                f"tables={len(bundle)}, size={size}bytes",
                entry_count=sum(len(v) for v in bundle.values()),
                bundle_size_bytes=size,
            )
        except Exception as e:
            return ForensicsReport("incident_bundle", False, time.monotonic() - start, str(e))
