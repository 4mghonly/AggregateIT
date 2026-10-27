"""B61 UTC+04 genuine seven-day edition lineage; structural checks only."""
from __future__ import annotations
from datetime import datetime,timedelta,timezone
from hashlib import sha256
import re

GST=timezone(timedelta(hours=4))
HEX=re.compile(r"^[0-9a-f]{64}$")
def _date(value):
    if not isinstance(value,str):raise ValueError("missing_edition_timestamp")
    try:d=datetime.fromisoformat(value.replace("Z","+00:00"))
    except ValueError:raise ValueError("invalid_edition_timestamp") from None
    if d.tzinfo is None or d.utcoffset() is None:raise ValueError("timezone_required")
    return d.astimezone(GST).date()

def evaluate_week_lineage(records, *,as_of:str):
    today=_date(as_of)
    if not isinstance(records,list) or len(records)>40:
        raise ValueError("invalid_week_input")
    seen=set(); days={"english":set(),"arabic":set()}
    content_digests={"english":set(),"arabic":set()}
    issues=[]
    for row in records:
        if not isinstance(row,dict) or row.get("product") not in days:
            raise ValueError("invalid_daily_receipt")
        name=row["product"];d=_date(row.get("slot_id"))
        if not today-timedelta(days=6)<=d<=today:
            raise ValueError("daily_receipt_outside_window")
        if (row.get("origin")!="original_source_capture" or
            row.get("held") is not True or row.get("production_sent") is not False):
            raise ValueError("untrusted_genuine_daily_status")
        digest=row.get("edition_sha256");src=row.get("source_snapshot_sha256")
        if not isinstance(digest,str) or not HEX.fullmatch(digest) or not isinstance(src,str) or not HEX.fullmatch(src):
            raise ValueError("missing_daily_source_digest")
        if (name,d) in seen:raise ValueError("duplicate_daily_product_date")
        seen.add((name,d))
        if digest in content_digests[name]:
            issues.append("reused_identical_edition_digest")
        content_digests[name].add(digest);days[name].add(d)
    counts={name:len(s) for name,s in days.items()}
    structural_complete=all(n==7 for n in counts.values()) and not issues
    return {"schema":"aggregateit-v2-b61-7day-lineage/1",
            "observed_days":counts,
            "missing_days":{p:[(today-timedelta(days=n)).isoformat()
                    for n in range(6,-1,-1) if today-timedelta(days=n) not in days[p]]
                    for p in days},
            "duplicate_or_replay_issues":sorted(set(issues)),
            "seven_distinct_days_structurally_present":structural_complete,
            "offhost_signed_source_snapshot_chain_verified":False,
            "full_real_weekly_editorial_quality_verified":False,
            "originally_delivered_daily_history_verified":False,
            "can_release":False}
