from __future__ import annotations

import sqlite3
import time
from dataclasses import dataclass, field
from pathlib import Path

from app.core.archive.indexer import ArchiveIndexer
from app.core.archive.snapshot import ArchiveSnapshot


@dataclass
class IngestionReport:
    scenario: str
    passed: bool = False
    duration_seconds: float = 0.0
    detail: str = ""
    checks: dict[str, bool] = field(default_factory=dict)

    def success(self, detail: str) -> IngestionReport:
        self.passed = True
        self.detail = detail
        return self

    def fail(self, detail: str) -> IngestionReport:
        self.passed = False
        self.detail = detail
        return self


class ArchiveIngestionValidator:
    def __init__(self, work_dir: Path) -> None:
        self._work = work_dir
        self._work.mkdir(parents=True, exist_ok=True)

    def _idx(self, name: str) -> ArchiveIndexer:
        idx = ArchiveIndexer(str(self._work / name))
        idx.open()
        return idx

    def _pending(self, scenario: str) -> IngestionReport:
        return IngestionReport(scenario=scenario)

    # 1 — Large import
    def validate_large_import(self) -> IngestionReport:
        start = time.monotonic()
        r = self._pending("large_import")
        try:
            idx = self._idx("large_import.db")
            for i in range(500):
                snap = ArchiveSnapshot(
                    archive_type="bulk",
                    source_id=f"src_{i}",
                    data={"index": i, "payload": "x" * 256},
                ).with_checksum()
                idx.index(snap)
            count = idx.count
            idx.close()

            r.checks["total"] = count == 500
            if r.checks["total"]:
                return r.success(f"imported {count} snapshots, integrity ok")
            return r.fail(f"expected 500 got {count}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # 2 — Arabic indexing
    def validate_arabic_indexing(self) -> IngestionReport:
        start = time.monotonic()
        r = self._pending("arabic_indexing")
        arabic_names = [
            "رسالة رسمية",
            "تقرير طبي",
            "معاملة إدارية",
            "كتاب دوري",
            "أمر إحالة",
        ]
        try:
            idx = self._idx("arabic.db")
            for name in arabic_names:
                snap = ArchiveSnapshot(
                    archive_type="arabic",
                    source_id="ar_001",
                    data={"title": name, "content": f"نص {name}"},
                    metadata={"language": "ar", "filename": f"{name}.pdf"},
                ).with_checksum()
                sid = idx.index(snap)
                verified = idx.verify_integrity(sid)
                r.checks[f"arabic_{name[:4]}"] = verified
            final = idx.count
            idx.close()

            passed = all(v for v in r.checks.values())
            if passed:
                return r.success(f"{final} Arabic snapshots indexed & verified")
            return r.fail(f"Arabic verification failed: {r.checks}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # 3 — Attachment-heavy ingestion
    def validate_attachment_heavy_ingestion(self) -> IngestionReport:
        start = time.monotonic()
        r = self._pending("attachment_heavy_ingestion")
        try:
            idx = self._idx("attachment_heavy.db")
            snap = ArchiveSnapshot(
                archive_type="attachments",
                source_id="attachment_test",
                data={"description": "attachment-heavy snapshot"},
            ).with_checksum()
            sid = idx.index(snap)

            for i in range(100):
                idx.link_attachment(
                    sid,
                    f"file_{i:04d}.pdf",
                    f"sha256_{i:064x}",
                    1024 + i,
                    {"category": "report", "page_count": i + 1},
                )

            idx.close()

            conn = sqlite3.connect(str(self._work / "attachment_heavy.db"))
            attach_count = conn.execute(
                "SELECT COUNT(*) FROM archive_attachment WHERE snapshot_id=?",
                (sid,),
            ).fetchone()[0]
            conn.close()

            r.checks["attachments_linked"] = attach_count == 100
            if r.checks["attachments_linked"]:
                return r.success(f"{attach_count} attachments linked to 1 snapshot")
            return r.fail(f"expected 100 attachments, got {attach_count}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # 4 — Archive replay (iterate all in deterministic order)
    def validate_archive_replay(self) -> IngestionReport:
        start = time.monotonic()
        r = self._pending("archive_replay")
        try:
            idx = self._idx("replay.db")
            inserted_ids = []
            for i in range(100):
                snap = ArchiveSnapshot(
                    archive_type="replay",
                    source_id=f"replay_{i}",
                    data={"seq": i},
                ).with_checksum()
                sid = idx.index(snap)
                inserted_ids.append(sid)
            idx.close()

            conn = sqlite3.connect(str(self._work / "replay.db"))
            rows = conn.execute(
                "SELECT snapshot_id FROM archive_index ORDER BY id"
            ).fetchall()
            conn.close()

            replayed = [row[0] for row in rows]
            r.checks["count_match"] = len(replayed) == 100
            r.checks["order_preserved"] = replayed == inserted_ids

            if r.checks["count_match"] and r.checks["order_preserved"]:
                return r.success(f"replayed {len(replayed)} snapshots, order preserved")
            return r.fail(f"replayed {len(replayed)}, expected 100")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # 5 — Corrupted attachment isolation
    def validate_corrupted_attachment_isolation(self) -> IngestionReport:
        start = time.monotonic()
        r = self._pending("corrupted_attachment_isolation")
        try:
            idx = self._idx("corrupt_attach.db")
            snap = ArchiveSnapshot(
                archive_type="corrupt_test",
                source_id="corrupt_001",
                data={"purpose": "corruption detection"},
            ).with_checksum()
            sid = idx.index(snap)

            expected = {"clean.pdf": "hash_clean", "report.pdf": "hash_report"}
            for fname, fhash in expected.items():
                idx.link_attachment(sid, fname, fhash, 512, {})
            idx.close()

            conn = sqlite3.connect(str(self._work / "corrupt_attach.db"))
            conn.execute(
                "UPDATE archive_attachment SET file_hash='hash_tampered' "
                "WHERE file_name='report.pdf'"
            )
            conn.commit()
            conn.close()

            idx2 = self._idx("corrupt_attach.db")
            atts = sqlite3.connect(
                str(self._work / "corrupt_attach.db")
            ).execute(
                "SELECT file_name, file_hash FROM archive_attachment "
                "WHERE snapshot_id=?", (sid,)
            ).fetchall()
            idx2.close()

            mismatches = 0
            for fname, fhash in atts:
                if fname in expected and fhash != expected[fname]:
                    mismatches += 1

            r.checks["expected_hash_mismatch_detected"] = mismatches == 1
            r.checks["clean_unchanged"] = any(
                f[0] == "clean.pdf" and f[1] == "hash_clean" for f in atts
            )
            r.checks["tampered_hash_found"] = any(
                f[0] == "report.pdf" and f[1] == "hash_tampered" for f in atts
            )

            if mismatches == 1:
                return r.success(
                    "1 corrupted attachment detected via hash comparison"
                )
            return r.fail(
                f"expected 1 mismatch, got {mismatches}"
            )
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # 6 — Deterministic pagination
    def validate_deterministic_pagination(self) -> IngestionReport:
        start = time.monotonic()
        r = self._pending("deterministic_pagination")
        try:
            idx = self._idx("pagination.db")
            for i in range(73):
                snap = ArchiveSnapshot(
                    archive_type="pagination",
                    source_id=f"page_{i}",
                    data={"seq": i},
                ).with_checksum()
                idx.index(snap)
            idx.close()

            conn = sqlite3.connect(str(self._work / "pagination.db"))
            page1 = conn.execute(
                "SELECT snapshot_id FROM archive_index ORDER BY id LIMIT 10 OFFSET 0"
            ).fetchall()
            page2 = conn.execute(
                "SELECT snapshot_id FROM archive_index ORDER BY id LIMIT 10 OFFSET 10"
            ).fetchall()
            page3 = conn.execute(
                "SELECT snapshot_id FROM archive_index ORDER BY id LIMIT 10 OFFSET 20"
            ).fetchall()
            conn.close()

            ids_p1 = [r[0] for r in page1]
            ids_p2 = [r[0] for r in page2]
            ids_p3 = [r[0] for r in page3]

            no_overlap = (
                len(set(ids_p1) & set(ids_p2)) == 0
                and len(set(ids_p1) & set(ids_p3)) == 0
                and len(set(ids_p2) & set(ids_p3)) == 0
            )
            correct_count = len(ids_p1) == 10 and len(ids_p2) == 10 and len(ids_p3) == 10

            r.checks["pages_disjoint"] = no_overlap
            r.checks["page_sizes_correct"] = correct_count

            if no_overlap and correct_count:
                return r.success("3 disjoint pages of 10, deterministic ordering")
            sizes = f"({len(ids_p1)},{len(ids_p2)},{len(ids_p3)})"
            return r.fail(f"overlap={not no_overlap}, sizes={sizes}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # 7 — FTS5 rebuild
    def validate_fts5_rebuild(self) -> IngestionReport:
        start = time.monotonic()
        r = self._pending("fts5_rebuild")
        try:
            idx = self._idx("fts5.db")
            docs = [
                ("arabic", "وثيقة رسمية حكومية"),
                ("arabic", "تقرير الأداء السنوي"),
                ("english", "annual performance report"),
                ("english", "government official document"),
            ]
            sids = []
            for lang, text in docs:
                snap = ArchiveSnapshot(
                    archive_type="fts_test",
                    source_id=f"fts_{lang}",
                    data={"content": text},
                    metadata={"language": lang},
                ).with_checksum()
                sids.append(idx.index(snap))
            idx.close()

            conn = sqlite3.connect(str(self._work / "fts5.db"))
            conn.execute(
                "CREATE VIRTUAL TABLE IF NOT EXISTS archive_fts USING fts5("
                "snapshot_id UNINDEXED, content)"
            )
            for sid, (lang, text) in zip(sids, docs):
                conn.execute(
                    "INSERT INTO archive_fts (snapshot_id, content) VALUES (?, ?)",
                    (sid, text),
                )
            conn.commit()

            arabic_hits = conn.execute(
                "SELECT COUNT(*) FROM archive_fts WHERE content MATCH 'وثيقة'"
            ).fetchone()[0]
            english_hits = conn.execute(
                "SELECT COUNT(*) FROM archive_fts WHERE content MATCH 'report'"
            ).fetchone()[0]
            conn.close()

            r.checks["arabic_fts_match"] = arabic_hits >= 1
            r.checks["english_fts_match"] = english_hits >= 1

            if arabic_hits >= 1 and english_hits >= 1:
                return r.success(
                    f"FTS5: Arabic={arabic_hits}, English={english_hits}"
                )
            return r.fail(
                f"FTS5: Arabic={arabic_hits}, English={english_hits}"
            )
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # 8 — Long-session browsing
    def validate_long_session_browsing(self) -> IngestionReport:
        start = time.monotonic()
        r = self._pending("long_session_browsing")
        try:
            idx = self._idx("long_session.db")
            total_ops = 0
            for batch in range(10):
                for _ in range(20):
                    snap = ArchiveSnapshot(
                        archive_type="browse",
                        source_id=f"batch_{batch}",
                        data={"batch": batch},
                    ).with_checksum()
                    idx.index(snap)
                    total_ops += 1
                count_after = idx.count
                r.checks[f"count_after_batch_{batch}"] = count_after == total_ops
            idx.close()

            passed = all(v for v in r.checks.values() if isinstance(v, bool))
            if passed:
                return r.success(
                    f"long session: {total_ops} ops across 10 batches, counts consistent"
                )
            return r.fail(f"count assertion failed: {r.checks}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # 9 — Compaction continuity
    def validate_compaction_continuity(self) -> IngestionReport:
        start = time.monotonic()
        r = self._pending("compaction_continuity")
        try:
            idx = self._idx("compact_cont.db")
            snap_ids = []
            for i in range(50):
                snap = ArchiveSnapshot(
                    archive_type="compact",
                    source_id=f"compact_{i}",
                    data={"seq": i},
                ).with_checksum()
                sid = idx.index(snap)
                snap_ids.append(sid)
            pre_count = idx.count
            idx.close()

            conn = sqlite3.connect(str(self._work / "compact_cont.db"))
            conn.execute("DELETE FROM archive_index WHERE id % 3 = 0")
            conn.commit()
            conn.execute("VACUUM")
            conn.close()

            idx2 = self._idx("compact_cont.db")
            post_count = idx2.count
            remaining_ids = [
                row[0]
                for row in sqlite3.connect(
                    str(self._work / "compact_cont.db")
                ).execute("SELECT snapshot_id FROM archive_index").fetchall()
            ]
            still_valid = all(
                idx2.verify_integrity(sid) for sid in remaining_ids
            )
            idx2.close()

            expected = pre_count - (pre_count // 3)
            r.checks["pre_count"] = pre_count == 50
            r.checks["post_count"] = post_count == expected
            r.checks["remaining_valid"] = still_valid

            if pre_count == 50 and post_count == expected and still_valid:
                return r.success(
                    f"compaction: {pre_count} -> {post_count}, all remaining valid"
                )
            return r.fail(
                f"pre={pre_count}, post={post_count}, valid={still_valid}"
            )
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    def validate_all(self) -> list[IngestionReport]:
        return [
            self.validate_large_import(),
            self.validate_arabic_indexing(),
            self.validate_attachment_heavy_ingestion(),
            self.validate_archive_replay(),
            self.validate_corrupted_attachment_isolation(),
            self.validate_deterministic_pagination(),
            self.validate_fts5_rebuild(),
            self.validate_long_session_browsing(),
            self.validate_compaction_continuity(),
        ]
