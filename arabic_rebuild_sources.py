"""Rebuild production source registry from the latest live compatibility audit."""
from __future__ import annotations

import json
from pathlib import Path

from arabic_newsletter.core import REGIONS

ROOT=Path(__file__).resolve().parent
SOURCES=ROOT/"arabic_newsletter"/"sources.json"
AUDIT=ROOT/"arabic_newsletter"/"SOURCE_AUDIT.json"

def main():
    rows=json.loads(SOURCES.read_text(encoding="utf-8"))
    audit=json.loads(AUDIT.read_text(encoding="utf-8"))
    by_id={r["id"]:r for r in audit.get("sources",[]) if r.get("id")}
    active_by_region={r:0 for r in REGIONS}

    for row in rows:
        result=by_id.get(row.get("id"))
        if not result:
            row["enabled"]=False
            row["verification_status"]="failed"
            row["retired_reason"]="missing_from_latest_source_audit"
            continue

        ok=bool(result.get("production_compatible"))
        row["enabled"]=ok
        row["verification_status"]="active" if ok else "failed"
        row["verified_at"]=audit.get("checked_at")
        row["verification_environment"]="GitHub Actions full source compatibility audit"
        row["compatibility"]={
          "adapter":row.get("adapter") or ("rss" if row.get("feed") else "none"),
          "http":result.get("feed_http"),
          "entries":result.get("entries",0),
          "recent_72h":result.get("recent_72h",0),
          "reason":result.get("reason"),
        }
        if ok:
            row.pop("retired_reason",None)
            region=row.get("region")
            if region in active_by_region:
                active_by_region[region]+=1
        else:
            row["retired_reason"]="source_audit_"+str(result.get("reason") or "incompatible")

    missing=[r for r,n in active_by_region.items() if n<2]
    if missing:
        raise SystemExit("Refusing registry rebuild; target regions below two compatible sources: "+",".join(missing))

    SOURCES.write_text(json.dumps(rows,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({
      "audit_checked_at":audit.get("checked_at"),
      "active_total":sum(1 for r in rows if r.get("enabled") and r.get("verification_status")=="active"),
      "active_by_region":active_by_region,
      "below_redundancy_target":[r for r,n in active_by_region.items() if n<2]
    },ensure_ascii=False,indent=2))

if __name__=="__main__":
    main()
