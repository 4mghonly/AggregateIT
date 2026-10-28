"""Compare independent hosted source-audit observations without claiming recovery."""
from __future__ import annotations
import json
import sys

def compare(previous, current):
    def by_name(rows):
        if not isinstance(rows,list):raise ValueError("invalid_audit")
        result={}
        for row in rows:
            if not isinstance(row,dict) or not isinstance(row.get("name"),str):
                raise ValueError("invalid_source")
            key=(row.get("kind"),row["name"])
            if key in result:raise ValueError("duplicate_source")
            result[key]=row
        return result
    before,after=by_name(previous),by_name(current)
    shared=before.keys() & after.keys()
    persistent=sorted([f"{k[0]}:{k[1]}" for k in shared if not before[k].get("ok") and not after[k].get("ok")])
    recovered=sorted([f"{k[0]}:{k[1]}" for k in shared if not before[k].get("ok") and after[k].get("ok")])
    newly_failed=sorted([f"{k[0]}:{k[1]}" for k in shared if before[k].get("ok") and not after[k].get("ok")])
    return {"schema":"aggregateit-v2-source-audit-diff/1","shared":len(shared),
            "persistent_failures":persistent,"recovered_once":recovered,
            "new_failures":newly_failed,"missing_from_current":len(before.keys()-after.keys()),
            "new_in_current":len(after.keys()-before.keys()),
            "safe_to_delete_source":False,"release_accepted":False}

if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("usage: python v2_source_audit_diff.py previous.json current.json")
    with open(sys.argv[1],encoding="utf-8") as f:previous=json.load(f)
    with open(sys.argv[2],encoding="utf-8") as f:current=json.load(f)
    print(json.dumps(compare(previous,current),indent=2))
