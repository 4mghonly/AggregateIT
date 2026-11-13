"""Persistent editorial history and evidence-bound seven-day intelligence for AggregateIT V2.

Development-only module: no sender, external API or model calls.
"""
from __future__ import annotations
import json
import sqlite3
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import urlsplit

_ALLOWED_TOPICS = {"geopolitics","security","military","diplomacy","political_stability","humanitarian_conflict","sanctions","strategic_infrastructure","markets","finance","energy","trade","cyber","policy","macro"}
_MIN_PRIORITY = 35

def compact_sections(sections):
    """Omit unpopulated content instead of rendering diagnostic blank panels."""
    return {name: value for name, value in sections.items() if value and (not isinstance(value,str) or value.strip())}

def _day(value):
    return date.fromisoformat(value)

def _validated_story(item):
    if not isinstance(item,dict):
        raise ValueError("invalid_story")
    required=("event_id","headline","region","summary","source_url","priority")
    if any(k not in item for k in required):
        raise ValueError("missing_story_fields")
    for key in ("event_id","headline","region","summary"):
        if not isinstance(item[key],str) or not item[key].strip() or len(item[key])>4000:
            raise ValueError("invalid_story_text")
    u=urlsplit(item["source_url"])
    if u.scheme!="https" or not u.hostname or u.username or u.password:
        raise ValueError("invalid_source_url")
    if type(item["priority"]) is not int or not 0<=item["priority"]<=100:
        raise ValueError("invalid_priority")
    if item.get("topic") and item["topic"] not in _ALLOWED_TOPICS:
        return None
    if item["priority"]<_MIN_PRIORITY:
        return None
    result={k:item[k] for k in required}|({"topic":item["topic"]} if item.get("topic") else {})
    for field in ("assessment","watch"):
        value=item.get(field)
        if value is not None:
            if not isinstance(value,str) or len(value)>1500:raise ValueError("invalid_analytical_field")
            if value.strip():result[field]=value.strip()
    if "assessment" in result or "watch" in result:
        if item.get("analysis_origin") not in ("v1_model_unverified","arabic_v2_model_unverified"):
            raise ValueError("missing_analytical_provenance")
        result["analysis_origin"]=item["analysis_origin"]
    return result

class ProductHistory:
    """Append-only date/event observations, retaining seven-day trend inputs."""
    def __init__(self,path):
        self.path=Path(path)
        self.path.parent.mkdir(parents=True,exist_ok=True)
        self.db=sqlite3.connect(self.path)
        self.db.execute("""CREATE TABLE IF NOT EXISTS observations (
          language TEXT NOT NULL, day TEXT NOT NULL, event_id TEXT NOT NULL,
          payload TEXT NOT NULL, PRIMARY KEY(language,day,event_id))""")
        self.db.execute("CREATE INDEX IF NOT EXISTS obs_day ON observations(language,day)")
        self.db.commit()
    def record(self,language,day,stories):
        if language not in ("en","ar") or not isinstance(stories,list) or len(stories)>2000:
            raise ValueError("invalid_edition")
        _day(day)
        unique={}
        for story in stories:
            valid=_validated_story(story)
            if valid is None:continue
            key=valid["event_id"]
            if key not in unique or valid["priority"]>unique[key]["priority"]:
                unique[key]=valid
        # Each day is immutable: reruns cannot silently rewrite history.
        with self.db:
            for key,story in unique.items():
                raw=json.dumps(story,ensure_ascii=False,sort_keys=True)
                prior=self.db.execute("SELECT payload FROM observations WHERE language=? AND day=? AND event_id=?",(language,day,key)).fetchone()
                if prior and prior[0]!=raw:
                    raise ValueError("conflicting_historical_observation")
                self.db.execute("INSERT OR IGNORE INTO observations VALUES(?,?,?,?)",(language,day,key,raw))
        return len(unique)
    def observations(self,language,start,end):
        if language not in ("en","ar"):raise ValueError("invalid_language")
        return [(d,json.loads(p)) for d,p in self.db.execute("SELECT day,payload FROM observations WHERE language=? AND day>=? AND day<=? ORDER BY day,event_id",(language,start,end))]
    def close(self):self.db.close()

def build_weekly_intelligence(history,language,as_of,max_events=30):
    end=_day(as_of)
    start=end-timedelta(days=6)
    grouped={}
    days=set()
    for day,story in history.observations(language,start.isoformat(),end.isoformat()):
        days.add(day)
        grouped.setdefault(story["event_id"],[]).append((day,story))
    events=[]
    for event_id,rows in grouped.items():
        rows.sort(key=lambda x:x[0])
        timeline=[]
        last_summary=None
        changes=0
        for day,story in rows:
            if story["summary"]!=last_summary:
                if last_summary is not None:changes+=1
                timeline.append({"date":day,"development":story["summary"],"source_url":story["source_url"]})
                last_summary=story["summary"]
        latest=rows[-1][1]
        events.append({"event_id":event_id,"headline":latest["headline"],"region":latest["region"],
                       "topic":latest.get("topic"),"priority":max(x[1]["priority"] for x in rows),
                       "observation_days":len({d for d,_ in rows}),"change_count":changes,
                       "timeline":timeline,"latest_summary":latest["summary"],
                       "assessment_text":latest.get("assessment"),"watch_text":latest.get("watch"),
                       "analysis_origin":latest.get("analysis_origin"),
                       "source_urls":sorted({x[1]["source_url"] for x in rows})})
    # Only infer observable patterns, never causation or forward predictions.
    for event in events:
        observations=event["observation_days"]
        changes=event["change_count"]
        event["assessment"]={
            "en":("Multiple source observations show a changed account of this development."
                  if changes else "The available observations do not establish a change in this development."),
            "ar":("تُظهر الملاحظات المتاحة تغيراً في الرواية المنشورة عن هذا التطور."
                  if changes else "لا تثبت الملاحظات المتاحة حدوث تغير في هذا التطور."),
            "evidence_days":observations,
            "change_observed":bool(changes),
            "limitation":"No causal inference, independent fact verification, or prediction established."
        }
    events.sort(key=lambda x:(-x["priority"],-x["change_count"],x["event_id"]))
    return {"language":language,"window_start":start.isoformat(),"window_end":end.isoformat(),
            "days_observed":len(days),"complete_week":len(days)==7,
            "events":events[:max_events],"total_events":len(events),
            "analysis_scope":"source-backed changes only; no invented implications"}
