"""B42 Somalia source-feed search; read-only, no source registration or posting.

Each static candidate URL gets one bounded HTTPS request using public-IP pinning.
Compatibility metrics follow the production audit's feedparser semantics while
freshness, duplicate publisher families and HTTPS article links are separate.
No source body, headline or article URL is serialized to the results.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime,timezone
from hashlib import sha256
from urllib.error import HTTPError
from urllib.parse import urlsplit
import argparse
import json
import re
import ssl
import socket
import feedparser

from arabic_source_audit import _recent_ts
from v2_secure_transport import pinned_https_fetch, _origin_and_path

CANDIDATES=(
    ("radio-ergo-existing","Radio Ergo","radio_ergo","so","https://radioergo.org/feed/","existing"),
    ("sonna-ar-retry","SONNA Arabic","sonna","ar","https://sonna.so/ar/feed/","existing_repair"),
    ("goobjoog-retry","Goobjoog","goobjoog","so","https://goobjoog.com/feed/","existing_repair"),
    ("shabelle","Shabelle Media Network","shabelle","so","https://shabellemedia.com/feed/","new"),
    ("puntland-post","Puntland Post","puntland_post","so","https://puntlandpost.net/feed/","new"),
    ("horseed-somali","Horseed Media","horseed","so","https://horseedmedia.net/category/somali-news/feed/","new"),
    ("somali-dispatch","Somali Dispatch","somali_dispatch","en","https://www.somalidispatch.com/feed/","new"),
    ("somali-digest","The Somali Digest","somali_digest","en","https://thesomalidigest.com/feed/","new"),
    ("sonna-en","SONNA English","sonna","en","https://sonna.so/en/feed/","alternate"),
    ("somali-guardian","Somali Guardian","somali_guardian","en","https://www.somaliguardian.com/feed/","new"),
    ("dalsan","Radio Dalsan","dalsan","so","https://radiodalsan.com/feed/","new"),
    ("caasimada","Caasimada Online","caasimada","so","https://www.caasimada.net/feed/","new"),
    ("goobjoog-en","Goobjoog English","goobjoog","en","https://en.goobjoog.com/feed/","alternate"),
    ("horseed-root","Horseed Media (root)","horseed","so","https://horseedmedia.net/feed/","alternate"),
)

def _https_article_link(value):
    if not isinstance(value,str) or len(value)>2048:return False
    try:
        p=urlsplit(value)
        return p.scheme=="https" and bool(p.hostname) and not p.username and not p.password
    except ValueError:return False

def assess_feed(data:bytes,*,observed_at:str)->dict:
    if not isinstance(data,bytes) or not 1<=len(data)<=1_000_000:raise ValueError("invalid_feed_size")
    moment=datetime.fromisoformat(observed_at.replace("Z","+00:00"))
    if moment.utcoffset() is None:raise ValueError("timezone_required")
    parsed=feedparser.parse(data)
    entries=list(parsed.entries or [])[:100]
    recent=0
    valid_urls=0
    dated=0
    unique=set()
    lang_samples=[]
    for item in entries:
        url=str(item.get("link","") or "")
        if _https_article_link(url) and url not in unique:
            unique.add(url);valid_urls+=1
        ts=_recent_ts(item)
        if ts is not None:
            dated+=1
            diff=moment.timestamp()-ts
            if 0<=diff<=259200:recent+=1
        if len(lang_samples)<8:
            lang_samples.append(str(item.get("title","") or "")[:240])
    arabic=sum(1 for c in "".join(lang_samples) if "\u0600"<=c<="\u06ff")
    latin=sum(1 for c in "".join(lang_samples) if "A"<=c<="Z" or "a"<=c<="z")
    production_compatible=bool(entries)
    # Strong candidate requires usable, recent, source-linked dated entries.
    fresh_candidate=(len(entries)>=3 and recent>=1 and valid_urls>=3 and dated>=1)
    return {"feed_entries":len(entries),"dated_entries":dated,"recent_72h":recent,
            "distinct_https_article_links":valid_urls,
            "bozo":bool(getattr(parsed,"bozo",False)),
            "arabic_title_chars_sample":arabic,
            "latin_title_chars_sample":latin,
            "production_audit_compatible":production_compatible,
            "recent_feed_candidate":fresh_candidate,
            "source_facts_verified":False,
            "raw_title_retained":False,"discord_sent":False}

def probe_one(info:tuple,*,observed_at:str,transport=pinned_https_fetch)->dict:
    cid,name,family,language,url,role=info
    row={"candidate_id":cid,"name":name,"publisher_family":family,
         "declared_language":language,"feed_url":url,"role":role,
         "status":"HOLD","production_audit_compatible":False,
         "recent_feed_candidate":False,"discord_sent":False}
    try:
        _origin_and_path(url)
        resp=transport(url,timeout=8,max_bytes=1_000_000,max_redirects=1,
            headers={"Accept":"application/rss+xml, application/atom+xml, application/xml, text/xml"})
        row["http_status"]=resp["status"]
        row["content_type"]=resp["content_type"][:90]
        row["final_feed_url"]=resp["final_url"]
        payload=resp["body"]
        row["feed_sha256"]=sha256(payload).hexdigest()
        row.update(assess_feed(payload,observed_at=observed_at))
        row["status"]="RECENT_CANDIDATE" if row["recent_feed_candidate"] else (
            "FEED_COMPATIBLE_STALE_OR_LOW_SIGNAL" if row["production_audit_compatible"] else "NO_ENTRIES")
    except Exception as exc:
        if isinstance(exc,HTTPError):
            row["failure_class"]="http_"+str(exc.code)
        elif isinstance(exc,(socket.timeout,TimeoutError)):
            row["failure_class"]="network_timeout"
        elif isinstance(exc,ssl.SSLError):
            row["failure_class"]="tls_verification"
        elif isinstance(exc,ValueError):
            row["failure_class"]="unsafe_or_invalid_xml"
        elif isinstance(exc,OSError):
            row["failure_class"]="network_unreachable"
        else:
            row["failure_class"]="parser_or_runtime_failure"
    return row

def roster_summary(rows:list[dict])->dict:
    if len(rows)!=len(CANDIDATES):raise ValueError("incomplete_candidate_roster")
    if len(set(r.get("candidate_id") for r in rows))!=len(rows):
        raise ValueError("duplicate_candidate_results")
    strong={}
    for row in rows:
        if row.get("status")=="RECENT_CANDIDATE" and row.get("recent_feed_candidate") is True:
            family=row["publisher_family"]
            if family not in strong or row["recent_72h"]>strong[family]["recent_72h"]:
                strong[family]=row
    return {"distinct_recent_publisher_families":len(strong),
            "technically_compatible_feed_urls":sum(r["production_audit_compatible"] is True for r in rows),
            "recent_candidate_feed_urls":sum(r["recent_feed_candidate"] is True for r in rows),
            "shortlist":[{"candidate_id":r["candidate_id"],"publisher_family":family,
                          "name":r["name"],"feed_url":r["feed_url"],
                          "recent_72h":r["recent_72h"],"feed_entries":r["feed_entries"]}
                         for family,r in sorted(strong.items())],
            "production_sources_unchanged":True,"source_registered":False,
            "automatic_promotion":False,"can_release":False}

def run()->dict:
    now=datetime.now(timezone.utc).isoformat()
    rows=[]
    with ThreadPoolExecutor(max_workers=4) as executor:
        jobs=[executor.submit(probe_one,item,observed_at=now) for item in CANDIDATES]
        for future in as_completed(jobs):rows.append(future.result())
    order={item[0]:idx for idx,item in enumerate(CANDIDATES)}
    rows.sort(key=lambda x:order[x["candidate_id"]])
    return {"schema":"aggregateit-v2-b42-somalia-feed-discovery/1","observed_at":now,
            "candidates":rows,"summary":roster_summary(rows),
            "raw_feed_bodies_retained":False,"article_facts_verified":False,
            "production_registry_modified":False,"discord_sent":False}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--output",required=True)
    args=ap.parse_args()
    report=run()
    from pathlib import Path
    path=Path(args.output);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print(json.dumps({"summary":report["summary"],
                      "statuses":[{"id":r["candidate_id"],"status":r["status"],
                                   "reason":r.get("failure_class"),"recent":r.get("recent_72h")}
                                  for r in report["candidates"]]},ensure_ascii=False))
if __name__=="__main__":main()
