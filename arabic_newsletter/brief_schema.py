"""Canonical Arabic briefing JSON contract.

The renderer consumes only this normalized structure. External model output never
creates the document and can only replace the analysis block after validation.
"""
from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timedelta, timezone

from arabic_newsletter.core import UAE, REGIONS, clean

SCHEMA_VERSION="arabic-brief-v3"
SEVERITIES={"low","medium","high","critical"}

def _text(value,limit):
    return clean(value)[:limit]

def _list_text(value,limit_items=6,limit_chars=420):
    if not isinstance(value,list):
        return []
    out=[]
    for item in value:
        item=_text(item,limit_chars)
        if item and item not in out:
            out.append(item)
        if len(out)>=limit_items:
            break
    return out

def deterministic_analysis(events):
    counts=Counter(REGIONS.get(e.get("region"),e.get("region") or "إقليمي") for e in events)
    leading="، ".join(name for name,_ in counts.most_common(4))
    return {
      "situation_ar":(
        "تتركز المواد المؤهلة في هذه الدورة ضمن: "
        +(leading or "عدة ساحات إقليمية")
        +". يعرض هذا الإصدار الوقائع المصدرية مباشرة، مع فصل التحليل عن الخبر."
      ),
      "implications_ar":"تُعطى الأولوية لأي انتقال موثق من التصريحات إلى إجراءات رسمية أو ميدانية قابلة للرصد.",
      "developing_ar":["تطورات ميدانية أو دبلوماسية قد تتغير مع صدور تأكيدات رسمية إضافية."],
      "watch_ar":["بيانات رسمية جديدة، تغيرات ميدانية موثقة، أو قيود على الحدود والمجال الجوي والممرات البحرية."]
    }

def normalize_source(src,index=0):
    if not isinstance(src,dict):
        src={}
    return {
      "id":_text(src.get("id") or src.get("source_id") or f"source-{index}",120),
      "source_id":_text(src.get("source_id") or src.get("id") or f"source-{index}",120),
      "source":_text(src.get("source") or "مصدر غير مسمى",160),
      "url":str(src.get("url") or "")[:1200],
      "published":src.get("published") if isinstance(src.get("published"),(int,float)) else 0,
      "affiliation":_text(src.get("affiliation") or "publisher",80),
      "kind":_text(src.get("kind") or "news",40),
      "country":_text(src.get("country") or "",12),
      "language":_text(src.get("language") or "ar",12),
      "region":_text(src.get("region") or "",40),
    }

def normalize_event(event,index):
    if not isinstance(event,dict):
        event={}
    sources=[normalize_source(s,i) for i,s in enumerate(event.get("sources") or []) if isinstance(s,dict)]
    source_ids=[s["id"] for s in sources if s["id"]]
    severity=_text(event.get("severity") or "medium",20).lower()
    if severity not in SEVERITIES:
        severity="medium"
    region=_text(event.get("region"),40)
    if region not in REGIONS:
        region="gcc"
    title=_text(event.get("title_ar"),100)
    summary=_text(event.get("summary_ar"),700)
    if title and title not in summary:
        first_source=sources[0]["source"] if sources else "المصدر"
        summary=_text(f"بحسب {first_source}، {title}. {summary}",700)
    return {
      "region":region,
      "topic":_text(event.get("topic") or "security",40),
      "title_ar":title,
      "summary_ar":summary or title,
      "assessment_ar":_text(event.get("assessment_ar"),500),
      "watch_ar":_text(event.get("watch_ar"),420),
      "severity":severity,
      "status_ar":_text(event.get("status_ar") or "تقرير منسوب",80),
      "fingerprint":_text(event.get("fingerprint") or f"event-{index}",180),
      "source_ids":source_ids,
      "sources":sources,
    }

def normalize_analysis(value,events):
    if not isinstance(value,dict):
        return deterministic_analysis(events)
    situation=_text(value.get("situation_ar"),1200)
    implications=_text(value.get("implications_ar"),1200)
    developing=_list_text(value.get("developing_ar"),5,420)
    watch=_list_text(value.get("watch_ar"),6,420)
    if not situation or not implications or not developing or not watch:
        return deterministic_analysis(events)
    return {
      "situation_ar":situation,
      "implications_ar":implications,
      "developing_ar":developing,
      "watch_ar":watch,
    }

def build_brief(events,health,input_count,window_hours=24,analysis=None,llm_health=None,previous_events=None):
    normalized=[normalize_event(e,i) for i,e in enumerate(events or [])]
    normalized=[e for e in normalized if e["title_ar"] and e["summary_ar"] and e["sources"]]
    now=datetime.now(timezone.utc).astimezone(UAE).replace(microsecond=0)
    start=now-timedelta(hours=window_hours)
    health_rows=health if isinstance(health,list) else []
    regions={}
    for r in REGIONS:
        healthy=sum(
          1 for row in health_rows
          if isinstance(row,dict) and row.get("region")==r and row.get("status")=="ok"
        )
        regions[r]={"healthy_extractors":healthy,"substitutes_used":0}
    unresolved=[r for r,v in regions.items() if not v["healthy_extractors"]]
    source_ids={s["id"] for e in normalized for s in e["sources"] if s["id"]}
    return {
      "schema_version":SCHEMA_VERSION,
      "sample":False,
      "window_start":start.isoformat(),
      "window_end":now.isoformat(),
      "events":normalized,
      "input_count":int(input_count or 0),
      "health":health_rows,
      "rejected":[],
      "analysis":normalize_analysis(analysis,normalized),
      "llm_health":llm_health if isinstance(llm_health,dict) else {"status":"not_attempted","routes":[]},
      "morning":now.hour<9,
      "coverage":{
        "event_source_count":len(source_ids),
        "event_source_languages":{"ar":len(source_ids)},
        "non_arabic_event_sources":0,
        "healthy_regions":[r for r,v in regions.items() if v["healthy_extractors"]],
        "active_extractors_by_region":{r:v["healthy_extractors"] for r,v in regions.items()},
        "substitutes_used":0,
        "unresolved_regions":unresolved,
        "coverage_degraded":bool(unresolved),
      },
      "source_health":{"regions":regions,"unresolved_regions":unresolved},
      "empty_cycle":not bool(normalized),
      "previous_events":previous_events if isinstance(previous_events,list) else [],
    }

def validate_brief(brief):
    errors=[]
    if not isinstance(brief,dict):
        return ["brief_not_object"]
    if brief.get("schema_version")!=SCHEMA_VERSION:
        errors.append("schema_version")
    if not isinstance(brief.get("events"),list):
        errors.append("events_not_list")
    else:
        for i,e in enumerate(brief["events"]):
            if not isinstance(e,dict):
                errors.append(f"event_{i}_not_object"); continue
            for key in ("region","title_ar","summary_ar","sources"):
                if not e.get(key):
                    errors.append(f"event_{i}_{key}")
            if not isinstance(e.get("sources"),list):
                errors.append(f"event_{i}_sources_not_list")
    a=brief.get("analysis")
    if not isinstance(a,dict):
        errors.append("analysis_not_object")
    else:
        for key in ("situation_ar","implications_ar","developing_ar","watch_ar"):
            if not a.get(key):
                errors.append("analysis_"+key)
    for key in ("coverage","source_health","llm_health"):
        if not isinstance(brief.get(key),dict):
            errors.append(key+"_not_object")
    return errors

def dumps(brief):
    errors=validate_brief(brief)
    if errors:
        raise ValueError("invalid_arabic_brief:"+",".join(errors))
    return json.dumps(brief,ensure_ascii=False,indent=2)
