"""Read-only candidate publisher article compatibility sampler.

Only article body structure is assessed. No articles are admitted to editorial
or released; original text is never logged or persisted.
"""
from __future__ import annotations
import json
from urllib.parse import urlsplit
from v2_secure_transport import pinned_https_fetch

def probe_articles(candidates,*,fetch=pinned_https_fetch):
 if not isinstance(candidates,(list,tuple)) or len(candidates)>8:raise ValueError("invalid_candidates")
 out=[]
 for p in candidates:
  if not isinstance(p,dict) or p.get("language") not in ("english","arabic"):raise ValueError("invalid_candidate")
  hosts=p.get("article_hosts");urls=p.get("article_urls")
  if not isinstance(hosts,list) or not hosts or not isinstance(urls,list) or len(urls)>3:raise ValueError("invalid_article_candidates")
  for url in urls:
   if not isinstance(url,str):raise ValueError("invalid_article_url")
   parsed=urlsplit(url)
   if parsed.scheme!="https" or parsed.hostname not in hosts or parsed.username or parsed.password or parsed.port not in (None,443):raise ValueError("article_host_mismatch")
  row={"publisher_id":p.get("publisher_id"),"language":p["language"],"attempts":0,"body_candidates":0,"status":"HOLD_NO_ARTICLE_URLS" if not urls else "HOLD_NO_VALIDATED_ARTICLE_BODY","onboarded":False}
  for url in urls:
   row["attempts"]+=1
   try:
    result=fetch(url,timeout=8,max_bytes=850000,max_redirects=1)
    body=result["body"]
    if not isinstance(body,bytes) or len(body)>850000:raise ValueError("invalid_html")
    from bs4 import BeautifulSoup
    soup=BeautifulSoup(body,"html.parser")
    for tag in soup(["script","style","nav","footer","header","aside"]):tag.decompose()
    paragraphs=[x.get_text(" ",strip=True) for x in soup.select("article p, main p")]
    good=[x for x in paragraphs if len(x)>=25]
    if len(good)>=2 and sum(map(len,good))>=80:row["body_candidates"]+=1
   except (OSError,ValueError,KeyError,TimeoutError):
    continue
  if row["body_candidates"]:row["status"]="HOLD_CANDIDATE_BODY_PRESENT_PARSER_AND_EVIDENCE_NOT_VALIDATED"
  out.append(row)
 return {"schema":"aggregateit-v2-b97-article-probe/1","sources":out,"can_release":False}

if __name__=="__main__":
 # Feed sampling deliberately separate from publisher onboarding.
 from v2_b97_live_source_probe import CANDIDATES
 import feedparser
 candidates=[]
 for p in CANDIDATES:
  urls=[]
  try:
   response=pinned_https_fetch(p["feed_url"],timeout=8,max_bytes=300000,max_redirects=1)
   for entry in feedparser.parse(response["body"]).entries[:20]:
    link=entry.get("link","")
    parsed=urlsplit(link)
    if parsed.scheme=="https" and parsed.hostname in p["article_hosts"] and link not in urls:urls.append(link)
    if len(urls)==3:break
  except (OSError,ValueError,KeyError,TimeoutError):pass
  candidates.append({**p,"article_urls":urls})
 print(json.dumps(probe_articles(candidates),ensure_ascii=False))
