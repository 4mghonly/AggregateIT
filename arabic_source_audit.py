"""Audit every Arabic briefing source for live compatibility."""
from __future__ import annotations

import concurrent.futures
import email.utils
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import feedparser
import requests

ROOT=Path(__file__).resolve().parent
SOURCES=ROOT/"arabic_newsletter"/"sources.json"
OUT=ROOT/"arabic_newsletter"/"SOURCE_AUDIT.json"

def _recent_ts(entry):
    for key in ("published_parsed","updated_parsed"):
        v=getattr(entry,key,None)
        if v:
            try: return datetime(*v[:6],tzinfo=timezone.utc).timestamp()
            except Exception: pass
    for key in ("published","updated"):
        raw=getattr(entry,key,None)
        if raw:
            try:
                dt=email.utils.parsedate_to_datetime(raw)
                if dt.tzinfo is None: dt=dt.replace(tzinfo=timezone.utc)
                return dt.timestamp()
            except Exception: pass
    return None

def probe(row):
    result={
      "id":row.get("id"),"name":row.get("name"),"region":row.get("region"),
      "country":row.get("country"),"language":row.get("language"),
      "enabled_before":bool(row.get("enabled")),
      "verification_status_before":row.get("verification_status"),
      "website_ok":False,"feed_configured":False,"feed_ok":False,
      "feed_http":None,"entries":0,"recent_72h":0,"bozo":False,
      "production_compatible":False,"reason":""
    }
    headers={"User-Agent":"AggregateIT-Source-Audit/1.0"}
    website=(row.get("website") or "").strip()
    if website.startswith("http"):
        try:
            r=requests.get(website,headers=headers,timeout=(5,12),allow_redirects=True)
            result["website_ok"]=r.status_code<500
            result["website_http"]=r.status_code
        except Exception as exc:
            result["website_error"]=type(exc).__name__
    feed=(row.get("feed") or "").strip()
    if not feed.startswith("http"):
        result["reason"]="no_feed"
        return result
    result["feed_configured"]=True
    try:
        r=requests.get(feed,headers=headers,timeout=(5,15),allow_redirects=True)
        result["feed_http"]=r.status_code
        result["feed_final_host"]=re.sub(r"^https?://([^/]+).*$",r"\1",r.url)
        if r.status_code!=200:
            result["reason"]=f"http_{r.status_code}"
            return result
        parsed=feedparser.parse(r.content)
        entries=list(parsed.entries or [])
        result["bozo"]=bool(getattr(parsed,"bozo",False))
        result["entries"]=len(entries)
        now=datetime.now(timezone.utc).timestamp()
        result["recent_72h"]=sum(1 for e in entries[:100] if (lambda t:t is not None and 0<=now-t<=259200)(_recent_ts(e)))
        if not entries:
            result["reason"]="zero_entries"
            return result
        sample=" ".join(str(getattr(e,"title","") or "") for e in entries[:8])
        result["arabic_chars"]=sum(1 for c in sample if "\u0600"<=c<="\u06ff")
        result["production_compatible"]=True
        result["feed_ok"]=True
        result["reason"]="ok"
        return result
    except Exception as exc:
        result["reason"]="exception_"+type(exc).__name__
        return result

def main():
    rows=json.loads(SOURCES.read_text(encoding="utf-8"))
    results=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
        futures={pool.submit(probe,row):row for row in rows}
        for fut in concurrent.futures.as_completed(futures):
            row=futures[fut]
            try:
                results.append(fut.result())
            except Exception as exc:
                results.append({
                  "id":row.get("id"),"name":row.get("name"),"region":row.get("region"),
                  "country":row.get("country"),"language":row.get("language"),
                  "enabled_before":bool(row.get("enabled")),
                  "verification_status_before":row.get("verification_status"),
                  "website_ok":False,"feed_configured":bool((row.get("feed") or "").startswith("http")),
                  "feed_ok":False,"feed_http":None,"entries":0,"recent_72h":0,"bozo":False,
                  "production_compatible":False,"reason":"audit_exception_"+type(exc).__name__
                })
    results.sort(key=lambda r:str(r.get("id") or ""))
    regions={}
    for r in results:
        region=r.get("region") or "unknown"
        d=regions.setdefault(region,{"compatible":0,"configured":0,"sources":[]})
        if r["feed_configured"]: d["configured"]+=1
        if r["production_compatible"]: d["compatible"]+=1
        d["sources"].append({"id":r["id"],"name":r["name"],"ok":r["production_compatible"],"reason":r["reason"]})
    payload={
      "checked_at":datetime.now(timezone.utc).isoformat(),
      "total":len(results),
      "compatible":sum(1 for r in results if r["production_compatible"]),
      "regions":regions,
      "sources":results,
    }
    OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"compatible":payload["compatible"],"total":payload["total"],
                      "regions":{k:v["compatible"] for k,v in regions.items()}},ensure_ascii=False))

if __name__=="__main__":
    main()
