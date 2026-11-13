"""Import genuine Arabic V2 briefing.json files or GitHub Actions ZIP artifacts."""
from __future__ import annotations
import argparse,hashlib,json,zipfile
from pathlib import Path
from urllib.parse import urlsplit
from v2_product_recovery import ProductHistory,build_weekly_intelligence
from v2_recovery_publication import render_recovery_html

def read_brief(path):
    path=Path(path)
    if path.suffix.lower()==".zip":
        with zipfile.ZipFile(path) as archive:
            if "briefing.json" not in archive.namelist():raise ValueError("missing_briefing_json")
            info=archive.getinfo("briefing.json")
            if info.file_size>5_000_000:raise ValueError("oversized_briefing")
            brief=json.loads(archive.read(info).decode("utf-8"))
    else:brief=json.loads(path.read_text(encoding="utf-8"))
    if brief.get("schema_version")!="arabic-brief-v3" or brief.get("sample") is True:
        raise ValueError("not_genuine_arabic_brief")
    day=brief["window_end"][:10]
    rows=[]
    for event in brief.get("events",[]):
        sources=event.get("sources") or []
        source=next((s for s in sources if isinstance(s,dict) and
                     isinstance(s.get("url"),str) and urlsplit(s["url"]).scheme=="https"),None)
        if source is None:continue
        title=event.get("title_ar")
        summary=event.get("summary_ar")
        if not isinstance(title,str) or not title.strip() or not isinstance(summary,str) or not summary.strip():continue
        identity=hashlib.sha256(source["url"].encode("utf-8")).hexdigest()[:24]
        assessment=event.get("assessment_ar")
        watch=event.get("watch_ar")
        extra={}
        if isinstance(assessment,str) and assessment.strip():extra["assessment"]=assessment[:1500]
        if isinstance(watch,str) and watch.strip():extra["watch"]=watch[:1500]
        if extra:extra["analysis_origin"]="arabic_v2_model_unverified"
        rows.append({"event_id":"source-"+identity,"headline":title[:300],
          "summary":summary[:1000],"region":event.get("region") or "unclassified",
          "priority":{"critical":95,"high":80,"medium":60,"low":40}.get(event.get("severity"),60),
          "topic":event.get("topic") or "geopolitics","source_url":source["url"],**extra})
    return day,rows

def import_arabic_briefs(paths,database,output_dir):
    captures=[read_brief(p) for p in paths]
    if not captures:raise ValueError("no_archives")
    h=ProductHistory(database)
    try:
        by_day={}
        for day,rows in captures:
            latest=by_day.setdefault(day,{})
            for row in rows:latest[row["event_id"]]=row
        imported=sum(h.record("ar",day,list(rows.values()))
                     for day,rows in sorted(by_day.items()))
        report=build_weekly_intelligence(h,"ar",max(day for day,_ in captures))
        out=Path(output_dir);out.mkdir(parents=True,exist_ok=True)
        (out/"arabic-weekly.html").write_text(render_recovery_html(report),encoding="utf-8")
        return {"imported":imported,"days_observed":report["days_observed"],
                "complete_week":report["complete_week"],"events":report["total_events"]}
    finally:h.close()

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("archives",nargs="+",type=Path)
    p.add_argument("--database",type=Path,required=True)
    p.add_argument("--output-dir",type=Path,required=True)
    a=p.parse_args()
    print(json.dumps(import_arabic_briefs(a.archives,a.database,a.output_dir),ensure_ascii=False))
