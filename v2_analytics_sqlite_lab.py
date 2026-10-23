"""B6 disposable SQLite analytics lab: IN MEMORY ONLY, not a D1 adapter.

No Cloudflare, persistent database, filesystem, Drive or deletion side effects.
Optional telemetry writes always require externally verified account headroom.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3

from v2_analytics_controls import budget_decision, validate_telemetry, retention_preview, _date

_DDL = """
CREATE TABLE op_events (
 idempotency_key TEXT PRIMARY KEY,
 kind TEXT NOT NULL,
 product TEXT NOT NULL CHECK(product IN ('arabic','english')),
 source_id TEXT,
 at TEXT NOT NULL,
 status TEXT NOT NULL,
 duration_ms INTEGER,
 attempts INTEGER,
 units INTEGER,
 canonical_json TEXT NOT NULL
);
CREATE INDEX op_events_date_idx ON op_events(at);
"""


class InMemoryAnalytics:
    def __init__(self):
        self._db = sqlite3.connect(":memory:")
        self._db.executescript(_DDL)
        self._local_writes_since_account_snapshot = 0
        self._local_bytes_since_account_snapshot = 0

    def ingest(self, row: dict, *, account_db_bytes: int | None,
               account_writes_today: int | None,
               account_reads_today: int | None) -> dict:
        event=validate_telemetry(row)
        payload=json.dumps(event,ensure_ascii=False,sort_keys=True,
                           separators=(",",":"),allow_nan=False)
        previous=self._db.execute(
            "SELECT canonical_json FROM op_events WHERE idempotency_key=?",
            (event["idempotency_key"],)
        ).fetchone()
        if previous is not None:
            if previous[0] != payload:
                raise ValueError("conflicting_analytics_idempotency_key")
            return {"status":"already_recorded", "db_written":False}
        decision=budget_decision(
            db_size_bytes=(account_db_bytes + self._local_bytes_since_account_snapshot
                           if account_db_bytes is not None else None),
            account_writes_today=(account_writes_today + self._local_writes_since_account_snapshot
                                  if account_writes_today is not None else None),
            account_reads_today=account_reads_today,
            proposed_writes=1, proposed_reads=1,
        )
        if not decision["permitted"]:
            return {"status":"withheld_optional_analytics",
                    "reason":decision["action"],"db_written":False}
        with self._db:
            self._db.execute(
                """INSERT INTO op_events
                   (idempotency_key,kind,product,source_id,at,status,
                    duration_ms,attempts,units,canonical_json)
                   VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (event["idempotency_key"],event["kind"],event["product"],
                 event.get("source_id"),event["at"],event["status"],
                 event.get("duration_ms"),event.get("attempts"),event.get("units"),payload),
            )
        self._local_writes_since_account_snapshot += 1
        self._local_bytes_since_account_snapshot += max(len(payload.encode("utf-8")) * 3, 4096)
        return {"status":"accepted_local_only", "db_written":True,
                "external_d1_written":False, "remaining_daily_writes":decision["write_remaining"]}

    def count(self) -> int:
        return self._db.execute("SELECT COUNT(*) FROM op_events").fetchone()[0]

    def rows(self) -> list[dict]:
        result=self._db.execute(
            "SELECT canonical_json FROM op_events ORDER BY at, idempotency_key"
        ).fetchall()
        return [json.loads(x[0]) for x in result]

    def metrics(self) -> list[dict]:
        data=self._db.execute(
            """SELECT product,kind,status,COUNT(*)
               FROM op_events GROUP BY product,kind,status
               ORDER BY product,kind,status"""
        ).fetchall()
        return [{"product":p,"kind":k,"status":s,"count":n}
                for p,k,s,n in data]

    def retention_dry_run(self, *, as_of: str) -> dict:
        rows=[{"id":r["idempotency_key"],"at":r["at"],
               "retention_class":"detail"} for r in self.rows()]
        return retention_preview(rows,as_of=as_of)

    def export_bytes(self, *, as_of: str) -> dict:
        _date(as_of)
        # Metadata only, never raw article URLs/prompt/response data.
        ordered=self.rows()
        records={"schema":"aggregateit-v2-local-telemetry/1",
                 "as_of":as_of,"rows":ordered}
        blob=json.dumps(records,ensure_ascii=False,sort_keys=True,
                        separators=(",",":"),allow_nan=False).encode("utf-8")
        return {"payload":blob,"sha256":hashlib.sha256(blob).hexdigest(),
                "row_count":len(ordered),"drive_uploaded":False,
                "production_backup":False}

    @staticmethod
    def verify_restore(export: dict) -> dict:
        if not isinstance(export,dict) or set(export) != {
            "payload","sha256","row_count","drive_uploaded","production_backup"
        }:
            raise ValueError("invalid_local_export")
        data=export["payload"]
        if not isinstance(data,bytes) or hashlib.sha256(data).hexdigest()!=export["sha256"]:
            raise ValueError("local_export_checksum_mismatch")
        if export["drive_uploaded"] is not False or export["production_backup"] is not False:
            raise ValueError("fake_external_backup_receipt")
        try:
            parsed=json.loads(data)
        except (ValueError,UnicodeDecodeError) as exc:
            raise ValueError("invalid_local_export_data") from exc
        if not isinstance(parsed,dict) or set(parsed)!={"schema","as_of","rows"} or parsed["schema"]!="aggregateit-v2-local-telemetry/1" or not isinstance(parsed["rows"],list) or len(parsed["rows"])>20000:
            raise ValueError("invalid_local_export_schema")
        # Read-only restore rehearsal into a new ephemeral database. No external DB.
        lab=InMemoryAnalytics()
        for row in parsed["rows"]:
            event=validate_telemetry(row)
            reply=lab.ingest(event,account_db_bytes=0,account_writes_today=0,
                             account_reads_today=0)
            if reply["status"]!="accepted_local_only":
                raise ValueError("duplicate_in_local_export")
        again=lab.export_bytes(as_of=parsed["as_of"])
        if again["sha256"]!=export["sha256"] or lab.count()!=export["row_count"]:
            raise ValueError("local_restore_not_identical")
        return {"restored_local_rows":lab.count(),"checksum_verified":True,
                "external_restore_verified":False,"in_memory_restore_only":True,
                "external_database_written":False,"external_backup_uploaded":False}
