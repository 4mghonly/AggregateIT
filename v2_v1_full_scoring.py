"""Side-effect-free English V1 keyword/watchlist relevance adapter."""
import json
import re
from pathlib import Path
from v2_keyword_priority import load_v1_keywords
ROOT=Path(__file__).resolve().parent
def _config(name):
 return json.loads((ROOT/"config"/name).read_text(encoding="utf-8"))
def _hit(text,term):
 return bool(re.search(r"(?<!\w)"+re.escape(term.casefold())+r"(?!\w)",text))
def score_english_v1(title,body="",*,source_name="",keyword_config=None,watchlist=None):
 """V1-inspired explainable score. Bounded to V2 priority range."""
 kw=keyword_config if keyword_config is not None else load_v1_keywords()
 watch=watchlist if watchlist is not None else _config("watchlist.json")
 text=(title+" "+body).casefold()
 components={"keyword":0,"ticker":0,"watchlist":0,"priority_source":0}
 hits=[]
 weights={"Critical":4,"High":3,"Medium":2,"Low":1}
 for cluster in kw["clusters"]:
  terms=cluster.get("phrases",[])
  if any(_hit(text,t) for t in terms if isinstance(t,str) and t):
   components["keyword"]+=weights.get(cluster.get("prio"),2)
   hits.append(cluster["id"])
 components["keyword"]=min(24,components["keyword"])
 # V1 symbol matches use strict boundaries; avoid matching ticker substrings.
 components["ticker"]=min(18,3*sum(_hit(text,t) for t in watch.get("tickers",[]) if re.fullmatch(r"[A-Z]{2,6}",t)))
 components["watchlist"]=min(12,2*sum(_hit(text,t) for t in watch.get("keywords",[]) if isinstance(t,str) and len(t)>2))
 if any(x in source_name.casefold() for x in ("reuters","associated press","bloomberg")):
  components["priority_source"]=5
 return {"priority":min(100,50+sum(components.values())),"components":components,"keyword_ids":hits}
