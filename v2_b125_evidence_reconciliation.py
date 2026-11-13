"""Independent B115/B120 run and manifest reconciliation; no release authorization.

Input must come from separately authenticated GitHub workflow run metadata.
This checks consistency, not publisher rights, model parity, or delivery parity.
"""
from datetime import date, datetime, timezone, timedelta
import re

SHA = re.compile(r"[0-9a-f]{40}\Z")
DIGEST = re.compile(r"[0-9a-f]{64}\Z")
BRANCH = "rebuild/aggregateit-v2"
WORKFLOW = ".github/workflows/v2-b80-b83-live-acceptance.yml"

def utc_stamp(raw):
    if not isinstance(raw,str):
        return None
    try:
        stamp=datetime.fromisoformat(raw.replace("Z","+00:00"))
        return stamp.astimezone(timezone.utc) if stamp.tzinfo is not None else None
    except ValueError:
        return None

def reconcile(pairs, rosters, runs, *, expected_sha):
    issues = []
    by_pair, by_roster, by_run = {}, {}, {}
    if not isinstance(expected_sha, str) or not SHA.fullmatch(expected_sha):
        issues.append("invalid_candidate_sha")
    for rows, target, name, key in ((pairs, by_pair, "pair", "github_run_id"),
                                    (rosters, by_roster, "roster", "github_run_id"),
                                    (runs, by_run, "run", "id")):
        if not isinstance(rows, list) or len(rows)>45:
            issues.append("invalid_"+name+"_collection")
            continue
        for row in rows:
            if not isinstance(row,dict):
                issues.append("invalid_"+name+"_row")
                continue
            identity=row.get(key)
            if identity in target:
                issues.append("duplicate_"+name+"_run")
            else:
                target[identity]=row
    valid_dates = []
    used_days = set()
    for run_id, pair in by_pair.items():
        roster=by_roster.get(run_id)
        try:
            run=by_run.get(int(run_id))
        except (ValueError,TypeError):
            run=None
        if not roster or not run:
            issues.append("missing_roster_or_authenticated_run")
            continue
        day=pair.get("utc_date")
        try:
            parsed=date.fromisoformat(day)
        except (ValueError,TypeError):
            issues.append("invalid_capture_date")
            continue
        if day in used_days:
            issues.append("duplicate_utc_date")
            continue
        used_days.add(day)
        observed=utc_stamp(pair.get("observed_at"))
        roster_observed=utc_stamp(roster.get("observed_at"))
        started=utc_stamp(run.get("run_started_at"))
        timing_ok=bool(observed and roster_observed and started and
                       observed==roster_observed and observed.date()==parsed and
                       -60 <= (observed-started).total_seconds() <= 7200)
        if (not timing_ok or roster.get("utc_date")!=day or
            run.get("path")!=WORKFLOW or run.get("event") not in ("workflow_dispatch","push")
            or pair.get("head_sha")!=expected_sha or roster.get("head_sha")!=expected_sha
            or run.get("head_sha")!=expected_sha
            or pair.get("input_manifest_sha256")!=roster.get("capture_sha256")
            or not isinstance(pair.get("input_manifest_sha256"),str)
            or not DIGEST.fullmatch(pair["input_manifest_sha256"])
            or run.get("head_branch")!=BRANCH
            or run.get("status")!="completed" or run.get("conclusion")!="success"):
            issues.append("provenance_or_manifest_mismatch")
            continue
        products=pair.get("products",{})
        roster_products=roster.get("products",{})
        if any(not isinstance(products.get(p),dict) or
               type(products[p].get("operational_v2_selected")) is not int or
               products[p]["operational_v2_selected"]<=0 or
               not isinstance(roster_products.get(p),dict) or
               type(roster_products[p].get("story_count")) is not int or
               roster_products[p]["story_count"]<=0 or
               len(roster_products[p].get("stories",[]))!=roster_products[p]["story_count"]
               for p in ("english","arabic")):
            issues.append("missing_actual_bilingual_selection")
            continue
        valid_dates.append(parsed)
    if set(by_roster)!=set(by_pair):
        issues.append("unpaired_roster")
    valid_dates.sort()
    consecutive=(len(valid_dates)==7 and
                 all(valid_dates[i+1]-valid_dates[i]==timedelta(days=1) for i in range(6)))
    complete=not issues and consecutive and len(by_pair)==7 and len(by_roster)==7 and len(by_run)==7
    return {"schema":"aggregateit-v2-b125-independent-reconciliation/1",
            "candidate_sha":expected_sha,
            "verified_dates":[d.isoformat() for d in valid_dates],
            "seven_verified":complete,
            "issues":sorted(set(issues+([] if consecutive else ["incomplete_consecutive_window"]))),
            "model_parity_verified":False,
            "visual_parity_verified":False,
            "delivery_parity_verified":False,
            "rights_verified":False,
            "can_release":False}
