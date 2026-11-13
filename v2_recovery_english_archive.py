"""Import genuine AggregateIT V1 English run.json artifact snapshots for V2 comparison."""
from __future__ import annotations
import argparse,json,zipfile
from pathlib import Path
from urllib.parse import urlsplit
from v2_product_recovery import ProductHistory,build_weekly_intelligence
from v2_recovery_publication import render_recovery_html

def read_run(path):
    path=Path(path)
    if path.suffix.lower()==".zip":
        with zipfile.ZipFile(path) as z:
            if "run.json" not in z.namelist():raise ValueError("missing_run_json")
            info=z.getinfo("run.json")
            if info.file_size>8_000_000:raise ValueError("oversized_run")
            run=json.loads(z.read(info).decode("utf-8"))
    else:run=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(run.get("events"),list) or not isinstance(run.get("run"),str):
        raise ValueError("invalid_v1_run")
    rows=[]
    for event in run["events"]:
        source=next((s for s in event.get("sources",[]) if isinstance(s,dict) and
                     isinstance(s.get("url"),str) and urlsplit(s["url"]).scheme=="https"),None)
        if source is None:continue
        title=event.get("title")
        if not isinstance(title,str) or not title.strip():continue
        change=event.get("what_changed")
        summary=title if not isinstance(change,str) or not change.strip() else title+" — "+change
        analysis=event.get("analysis") if isinstance(event.get("analysis"),dict) else {}
        assessment=analysis.get("assessment")
        extra={"assessment":assessment[:1500],"analysis_origin":"v1_model_unverified"} if isinstance(assessment,str) and assessment.strip() else {}
        rows.append({"event_id":"v1-"+str(event.get("event_id") or source["url"])[:100],
          "headline":title[:300],"summary":summary[:1000],
          "region":str(event.get("entity") or "global")[:100],
          "priority":{"Critical":95,"High":80,"Medium":60,"Low":40}.get(event.get("importance"),60),
          "topic":"geopolitics","source_url":source["url"],**extra})
    return run["run"][:10],rows

def import_english_runs(paths,database,output_dir):
    captures=[read_run(p) for p in paths]
    if not captures:raise ValueError("no_archives")
    by_day={}
    for day,rows in captures:
        latest=by_day.setdefault(day,{})
        for row in rows:latest[row["event_id"]]=row
    h=ProductHistory(database)
    try:
        imported=sum(h.record("en",day,list(rows.values())) for day,rows in sorted(by_day.items()))
        report=build_weekly_intelligence(h,"en",max(by_day))
        out=Path(output_dir);out.mkdir(parents=True,exist_ok=True)
        html=render_recovery_html(report)
        html=html.replace("<main>","<main><aside style='padding:16px;border:2px solid #a16b45'>V1 comparison baseline — not V2 English editorial history</aside>",1)
        (out/"english-weekly.html").write_text(html,encoding="utf-8")
        return {"imported":imported,"days_observed":report["days_observed"],
                "complete_week":report["complete_week"],"events":report["total_events"]}
    finally:h.close()

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("archives",nargs="+",type=Path)
    p.add_argument("--database",type=Path,required=True)
    p.add_argument("--output-dir",type=Path,required=True)
    a=p.parse_args()
    print(json.dumps(import_english_runs(a.archives,a.database,a.output_dir),ensure_ascii=False))
