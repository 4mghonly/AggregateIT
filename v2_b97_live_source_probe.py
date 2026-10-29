"""Read-only bounded candidate feed probe; never admits an untested article parser."""
from __future__ import annotations
import json
from urllib.parse import urlsplit
from v2_secure_transport import pinned_https_fetch

CANDIDATES=(
 {"publisher_id":"dw-en","language":"english","feed_url":"https://rss.dw.com/rdf/rss-en-world","article_hosts":["www.dw.com"]},
 {"publisher_id":"bbc-ar","language":"arabic","feed_url":"https://feeds.bbci.co.uk/arabic/rss.xml","article_hosts":["www.bbc.com","www.bbc.co.uk"]},
)

def probe(candidates,*,fetch=pinned_https_fetch):
 if not isinstance(candidates,(list,tuple)) or len(candidates)>8:raise ValueError("invalid_probe_candidates")
 results=[]
 for item in candidates:
  if not isinstance(item,dict) or item.get("language") not in ("english","arabic") or not isinstance(item.get("publisher_id"),str) or not item["publisher_id"]:raise ValueError("invalid_probe_candidate")
  url=item.get("feed_url")
  if not isinstance(url,str):raise ValueError("invalid_probe_url")
  p=urlsplit(url)
  if p.scheme!="https" or not p.hostname or p.username or p.password or p.port not in (None,443):raise ValueError("unsafe_probe_url")
  hosts=item.get("article_hosts")
  if not isinstance(hosts,list) or not hosts or any(not isinstance(h,str) or not h or h=="localhost" for h in hosts):raise ValueError("invalid_article_hosts")
  row={"publisher_id":item["publisher_id"],"language":item["language"],"feed_host":p.hostname,"status":"HOLD_FEED_FETCH_FAILED","onboarded":False,"article_body_gate_verified":False}
  try:
   result=fetch(url,timeout=8,max_bytes=300000,max_redirects=1)
   body=result["body"]
   if not isinstance(body,bytes) or not body or len(body)>300000:raise ValueError("invalid_feed_bytes")
   import feedparser
   parsed=feedparser.parse(body)
   entries=parsed.get("entries",[])
   row["feed_items_seen"]=min(len(entries),100)
   row["status"]="HOLD_ARTICLE_BODY_GATE_NOT_VALIDATED" if entries else "HOLD_FEED_EMPTY_OR_UNPARSEABLE"
  except (OSError,ValueError,KeyError,TimeoutError) as exc:
   row["failure_class"]=type(exc).__name__
  results.append(row)
 return {"schema":"aggregateit-v2-b97-live-probe/1","sources":results,"can_release":False,"production_modified":False}

if __name__=="__main__":
 print(json.dumps(probe(CANDIDATES),ensure_ascii=False))
