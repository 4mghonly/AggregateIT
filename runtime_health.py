"""Sanitized operational checks; delivery success is separate from content health."""
from datetime import datetime, timezone


def arabic_health(brief, selected):
    llm=brief.get("llm_health",{})
    translation=llm.get("translation",{})
    issues=[]
    if translation.get("status")!="ok": issues.append("translation incomplete")
    if llm.get("status")!="ok": issues.append("LLM analysis unavailable")
    if not brief.get("events"): issues.append("no eligible events")
    if not any(x.get("country")=="AE" for x in selected): issues.append("UAE coverage missing")
    unresolved=brief.get("coverage",{}).get("unresolved_regions",[])
    if unresolved: issues.append("source coverage gaps: "+",".join(unresolved))
    return {"checked_at":datetime.now(timezone.utc).isoformat(),
            "status":"degraded" if issues else "ok","issues":issues,
            "translation":translation,"analysis_status":llm.get("status"),
            "delivery":{"confirmed":False}}


def overdue_runs(runs,now=None):
    """Allow normal scheduler jitter, report runs older than operational tolerance."""
    now=now or datetime.now(timezone.utc)
    limits={"News Intelligence Engine":2*3600,
            "Arabic Briefing V2 Production":7*3600,
            "Intelligence Slide Deck":26*3600}
    issues=[]
    for name,limit in limits.items():
        matching=[r for r in runs if r.get("name")==name and r.get("status")=="completed" and r.get("conclusion")=="success"]
        dates=[datetime.fromisoformat(r["created_at"].replace("Z","+00:00")) for r in matching]
        if not dates or (now-max(dates)).total_seconds()>limit:
            issues.append(name+": overdue or no successful run")
    return issues
