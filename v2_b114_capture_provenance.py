"""B114: preserve daily historical capture provenance without counting reruns as days.

This is a diagnostic only. B95 strict legacy consolidation remains unchanged
and remains fail-closed. A distinct GitHub run is not a distinct UTC date.
"""
from __future__ import annotations
from datetime import date,timedelta
from pathlib import Path
import json,re

_NAMED_RUN=re.compile(r"^(?P<run>[0-9]{8,16})-(?P<day>\d{4}-\d{2}-\d{2})\.json$")
_LOCAL=re.compile(r"^\d{4}-\d{2}-\d{2}\.json$")
_DIGEST=re.compile(r"^[0-9a-f]{64}$")

def inspect_slots(directory:Path,*,today:date)->dict:
    root=Path(directory)
    files=sorted(root.glob("*.json")) if root.exists() else []
    if len(files)>60:raise ValueError("history_file_limit")
    captures={};invalid_sources=[]
    for file in files:
        if file.is_symlink() or file.stat().st_size>65536:raise ValueError("unsafe_history_file")
        item=json.loads(file.read_bytes())
        if not isinstance(item,dict) or item.get("schema")!="aggregateit-v2-b95-daily-history/1" or item.get("can_release") is not False:
            raise ValueError("untrusted_history_receipt")
        day=item.get("day")
        if not isinstance(day,str):raise ValueError("invalid_history_day")
        stamp=date.fromisoformat(day)
        if stamp>today or stamp<today-timedelta(days=29):raise ValueError("out_of_retention")
        counts=item.get("stories");digest=item.get("evidence_sha256")
        if (not isinstance(counts,dict) or set(counts)!={"english","arabic"}
            or any(type(x)!=int or not 0<=x<=30 for x in counts.values())
            or not isinstance(digest,str) or not _DIGEST.fullmatch(digest)):
            raise ValueError("invalid_history_receipt")
        match=_NAMED_RUN.fullmatch(file.name)
        if match:
            if match.group("day")!=day:raise ValueError("run_filename_date_mismatch")
            run_id=match.group("run")
        elif _LOCAL.fullmatch(file.name) and file.stem==day:
            run_id=None
        else:
            raise ValueError("unrecognized_capture_filename")
        captures.setdefault(day,[]).append({"run_id":run_id,"stories":counts,"evidence_sha256":digest})
    slot_conflicts=[]
    independent_days=set();different_same_day=[]
    for day,items in sorted(captures.items()):
        by_run={}
        for item in items:
            run=item["run_id"]
            if run is None:continue
            version=(item["evidence_sha256"],item["stories"]["english"],item["stories"]["arabic"])
            if run in by_run and by_run[run]!=version:
                slot_conflicts.append(day)
            by_run[run]=version
        if by_run:independent_days.add(day)
        if len(set(by_run.values()))>1:different_same_day.append(day)
    days=sorted(independent_days)
    seven=[(today-timedelta(days=i)).isoformat() for i in range(6,-1,-1)]
    return {"schema":"aggregateit-v2-b114-capture-provenance/1",
            "receipt_files":len(files),
            "captured_run_slots":sum(item["run_id"] is not None for items in captures.values() for item in items),
            "distinct_run_dates":days,
            "distinct_run_days_count":len(days),
            "independent_capture_variants_same_day":different_same_day,
            "same_run_day_conflicts":sorted(set(slot_conflicts)),
            "seven_day_window":seven,
            "seven_distinct_dates_with_capture":all(d in independent_days for d in seven),
            "v1_full_editorial_receipts_verified":False,
            "source_input_identity_verified":False,
            "release_readiness":"HOLD_REAL_COMPARISON_MISSING",
            "can_release":False}
if __name__=="__main__":
    import argparse
    from datetime import datetime,timezone
    parser=argparse.ArgumentParser()
    parser.add_argument("--directory",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    result=inspect_slots(args.directory,today=datetime.now(timezone.utc).date())
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf8")
    print(json.dumps({"distinct_run_days_count":result["distinct_run_days_count"],
                      "captured_run_slots":result["captured_run_slots"],
                      "seven_distinct_dates_with_capture":result["seven_distinct_dates_with_capture"],
                      "can_release":False}))
