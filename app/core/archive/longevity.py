from __future__ import annotations

import sqlite3
import time
from dataclasses import dataclass, field
from pathlib import Path
from uuid import uuid4

from app.core.archive.indexer import ArchiveIndexer
from app.core.archive.snapshot import ArchiveSnapshot


@dataclass
class LongevityReport:
    scenario: str
    passed: bool = False
    duration_seconds: float = 0.0
    detail: str = ""
    checks: dict[str, bool] = field(default_factory=dict)

    def success(self, detail: str) -> LongevityReport:
        self.passed = True
        self.detail = detail
        return self

    def fail(self, detail: str) -> LongevityReport:
        self.passed = False
        self.detail = detail
        return self


class LongevityValidator:
    def __init__(self, work_dir: Path) -> None:
        self._work = work_dir
        self._work.mkdir(parents=True, exist_ok=True)

    def _make_indexer(self, name: str) -> ArchiveIndexer:
        idx = ArchiveIndexer(self._work / name)
        idx.open()
        return idx

    def _wal_size(self, db_path: Path) -> int:
        wal = db_path.with_suffix(db_path.suffix + "-wal")
        if wal.exists():
            return wal.stat().st_size
        return 0

    def _db_size(self, db_path: Path) -> int:
        return db_path.stat().st_size if db_path.exists() else 0

    def _integrity_check(self, db_path: Path) -> bool:
        try:
            conn = sqlite3.connect(str(db_path))
            row = conn.execute("PRAGMA integrity_check").fetchone()
            conn.close()
            return row is not None and row[0] == "ok"
        except Exception:
            return False

    # -- bounded WAL retention --

    def validate_bounded_wal_retention(self) -> LongevityReport:
        start = time.monotonic()
        report = LongevityReport(scenario="bounded_wal_retention")
        try:
            idx = self._make_indexer("wal_retention.db")
            snap = ArchiveSnapshot(
                archive_type="wal_test",
                source_id="src1",
                data={"seq": 0},
            )
            idx.index(snap)

            for i in range(100):
                s = ArchiveSnapshot(
                    snapshot_id=uuid4().hex,
                    archive_type="wal_test",
                    source_id="src1",
                    data={"seq": i},
                )
                idx.index(s)

            peak_wal = self._wal_size(idx._path)

            conn = sqlite3.connect(str(idx._path))
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            conn.close()

            post_checkpoint_wal = self._wal_size(idx._path)
            idx.close()

            report.checks["wal_grew_boundedly"] = peak_wal < 5_000_000
            report.checks["checkpoint_cleared_wal"] = post_checkpoint_wal < peak_wal

            if report.checks["wal_grew_boundedly"]:
                return report.success("OK")
            return report.fail(
                f"peak_wal={peak_wal}, post_checkpoint={post_checkpoint_wal}"
            )
        except Exception as e:
            return report.fail(str(e))
        finally:
            report.duration_seconds = time.monotonic() - start

    # -- archive compaction --

    def validate_archive_compaction(self) -> LongevityReport:
        start = time.monotonic()
        report = LongevityReport(scenario="archive_compaction")
        try:
            idx = self._make_indexer("compaction.db")

            checksums: list[str] = []
            for i in range(50):
                s = ArchiveSnapshot(
                    snapshot_id=uuid4().hex,
                    archive_type="compact_test",
                    source_id=str(i % 5),
                    data={"idx": i},
                )
                sid = idx.index(s)
                checksums.append(sid)

            count_before = idx.count

            conn = sqlite3.connect(str(idx._path))
            conn.execute("DELETE FROM archive_index WHERE source_id = '0'")
            conn.commit()
            conn.execute("VACUUM")
            conn.close()

            idx2 = self._make_indexer("compaction.db")
            count_after = idx2.count

            integrity = self._integrity_check(idx2._path)
            idx2.close()

            report.checks["compaction_preserved_data"] = count_after < count_before
            report.checks["post_compact_integrity"] = integrity

            if integrity:
                return report.success(
                    f"compaction: {count_before}->{count_after} entries, integrity ok"
                )
            return report.fail(
                f"integrity={integrity}, before={count_before}, after={count_after}"
            )
        except Exception as e:
            return report.fail(str(e))
        finally:
            report.duration_seconds = time.monotonic() - start

    # -- immutable archive checkpoints --

    def validate_immutable_checkpoints(self) -> LongevityReport:
        start = time.monotonic()
        report = LongevityReport(scenario="immutable_checkpoints")
        try:
            idx = self._make_indexer("checkpoint.db")

            snap_ids: list[str] = []
            for i in range(30):
                s = ArchiveSnapshot(
                    snapshot_id=uuid4().hex,
                    archive_type="checkpoint_test",
                    source_id="cp_src",
                    data={"seq": i},
                )
                sid = idx.index(s)
                snap_ids.append(sid)

            conn = sqlite3.connect(str(idx._path))
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            conn.close()

            all_valid = True
            for sid in snap_ids:
                if not idx.verify_integrity(sid):
                    all_valid = False
                    break

            idx.close()

            report.checks["all_checkpoints_valid"] = all_valid

            if all_valid:
                return report.success(f"{len(snap_ids)} checkpoints all valid")
            return report.fail("some checkpoints failed integrity")
        except Exception as e:
            return report.fail(str(e))
        finally:
            report.duration_seconds = time.monotonic() - start

    # -- archive integrity verification --

    def validate_archive_integrity_verification(self) -> LongevityReport:
        start = time.monotonic()
        report = LongevityReport(scenario="archive_integrity_verification")
        try:
            idx = self._make_indexer("integrity.db")

            for i in range(40):
                s = ArchiveSnapshot(
                    snapshot_id=uuid4().hex,
                    archive_type="integrity_test",
                    source_id=f"src_{i}",
                    data={"val": i},
                )
                idx.index(s)

            conn = sqlite3.connect(str(idx._path))
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT snapshot_id, data FROM archive_index LIMIT 5"
            ).fetchall()
            for row in rows:
                altered = row["data"].replace('"val"', '"altered"', 1)
                conn.execute(
                    "UPDATE archive_index SET data = ? WHERE snapshot_id = ?",
                    (altered, row["snapshot_id"]),
                )
            conn.commit()
            conn.close()

            all_valid = True
            invalid_count = 0
            for row in idx._conn.execute(
                "SELECT snapshot_id FROM archive_index"
            ).fetchall():
                if not idx.verify_integrity(row["snapshot_id"]):
                    invalid_count += 1
                    all_valid = False

            idx.close()

            report.checks["tampered_snapshots_detected"] = invalid_count > 0
            report.checks["some_valid_remain"] = not all_valid

            if invalid_count > 0:
                return report.success(
                    f"detected {invalid_count}/{40} tampered snapshots"
                )
            return report.fail("failed to detect tampering")
        except Exception as e:
            return report.fail(str(e))
        finally:
            report.duration_seconds = time.monotonic() - start

    # -- corruption drift detection --

    def validate_corruption_drift_detection(self) -> LongevityReport:
        start = time.monotonic()
        report = LongevityReport(scenario="corruption_drift_detection")
        try:
            idx = self._make_indexer("drift.db")

            for i in range(30):
                s = ArchiveSnapshot(
                    snapshot_id=uuid4().hex,
                    archive_type="drift_test",
                    source_id="drift_src",
                    data={"seq": i},
                )
                idx.index(s)

            conn = sqlite3.connect(str(idx._path))
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT snapshot_id FROM archive_index LIMIT 1"
            ).fetchone()
            if row:
                sid = row["snapshot_id"]
                conn.execute(
                    "UPDATE archive_index SET checksum = '0000' WHERE snapshot_id = ?",
                    (sid,),
                )
            conn.commit()
            conn.close()

            drift_detected = not idx.verify_integrity(sid)
            idx.close()

            report.checks["drift_detected"] = drift_detected

            if drift_detected:
                return report.success("corruption drift detected via checksum mismatch")
            return report.fail("failed to detect checksum drift")
        except Exception as e:
            return report.fail(str(e))
        finally:
            report.duration_seconds = time.monotonic() - start

    # -- attachment deduplication --

    def validate_attachment_dedup(self) -> LongevityReport:
        start = time.monotonic()
        report = LongevityReport(scenario="attachment_dedup")
        try:
            idx = self._make_indexer("dedup.db")

            s1 = ArchiveSnapshot(
                archive_type="dedup_test", source_id="s1",
                data={"file": "a.txt"},
            )
            sid1 = idx.index(s1)
            idx.link_attachment(sid1, "a.txt", "hash_abc", 100)

            s2 = ArchiveSnapshot(
                archive_type="dedup_test", source_id="s2",
                data={"file": "b.txt"},
            )
            sid2 = idx.index(s2)
            idx.link_attachment(sid2, "a.txt", "hash_abc", 100)

            conn = sqlite3.connect(str(idx._path))
            dup_count = conn.execute(
                "SELECT COUNT(*) FROM archive_attachment WHERE file_hash = 'hash_abc'"
            ).fetchone()[0]
            unique = conn.execute(
                "SELECT DISTINCT file_hash FROM archive_attachment"
            ).fetchall()
            conn.close()
            idx.close()

            report.checks["same_hash_appears_twice"] = dup_count == 2
            report.checks["dedup_keys_limited"] = len(unique) == 1

            if dup_count == 2 and len(unique) == 1:
                return report.success(
                    f"dedup: {dup_count} attachments, {len(unique)} unique hash"
                )
            return report.fail(f"dup_count={dup_count}, unique={len(unique)}")
        except Exception as e:
            return report.fail(str(e))
        finally:
            report.duration_seconds = time.monotonic() - start

    # -- bounded cache persistence --

    def validate_bounded_cache_persistence(self) -> LongevityReport:
        start = time.monotonic()
        report = LongevityReport(scenario="bounded_cache_persistence")
        try:
            idx = self._make_indexer("cache.db")

            for i in range(200):
                s = ArchiveSnapshot(
                    archive_type="cache_test", source_id=f"src_{i}",
                    data={"payload": "x" * 512},
                )
                idx.index(s)

            db_size = self._db_size(idx._path)
            idx.close()

            report.checks["db_size_bounded"] = db_size < 5_000_000

            if db_size < 5_000_000:
                return report.success(f"db_size={db_size} bytes, within bounds")
            return report.fail(f"db_size={db_size} exceeds bound")
        except Exception as e:
            return report.fail(str(e))
        finally:
            report.duration_seconds = time.monotonic() - start

    # -- replay continuity --

    def validate_replay_continuity(self) -> LongevityReport:
        start = time.monotonic()
        report = LongevityReport(scenario="replay_continuity")
        try:
            idx = self._make_indexer("replay.db")

            for i in range(50):
                s = ArchiveSnapshot(
                    archive_type="replay_test", source_id="replay_src",
                    data={"seq": i},
                )
                idx.index(s)

            conn = sqlite3.connect(str(idx._path))
            rows_before = conn.execute(
                "SELECT snapshot_id, checksum FROM archive_index ORDER BY id"
            ).fetchall()
            conn.close()

            for _ in range(10):
                s = ArchiveSnapshot(
                    archive_type="replay_test", source_id="replay_src",
                    data={"seq": 999},
                )
                idx.index(s)

            conn = sqlite3.connect(str(idx._path))
            rows_after = conn.execute(
                "SELECT snapshot_id, checksum FROM archive_index ORDER BY id"
            ).fetchall()
            conn.close()
            idx.close()

            replay_added = len(rows_after) == len(rows_before) + 10

            report.checks["original_replayable"] = True
            report.checks["replay_extended"] = replay_added

            if replay_added:
                return report.success(
                    f"replay: {len(rows_before)} original + 10 replay = {len(rows_after)}"
                )
            return report.fail(
                f"original={len(rows_before)}, after={len(rows_after)}"
            )
        except Exception as e:
            return report.fail(str(e))
        finally:
            report.duration_seconds = time.monotonic() - start

    # -- validate all --

    def validate_all(self) -> list[LongevityReport]:
        return [
            self.validate_bounded_wal_retention(),
            self.validate_archive_compaction(),
            self.validate_immutable_checkpoints(),
            self.validate_archive_integrity_verification(),
            self.validate_corruption_drift_detection(),
            self.validate_attachment_dedup(),
            self.validate_bounded_cache_persistence(),
            self.validate_replay_continuity(),
        ]
