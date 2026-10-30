"""Conservative V1 keyword relevance bridge; no generated facts or geography quotas."""
from __future__ import annotations
import json
import re
from pathlib import Path

CONFIG_PATH=Path(__file__).resolve().parent/"config"/"keywords.json"
WEIGHTS={"Critical":30,"High":22,"Medium":12,"Low":6}

def load_v1_keywords(path=CONFIG_PATH):
    data=json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data,dict) or not isinstance(data.get("clusters"),list):
        raise ValueError("invalid_v1_keywords")
    return data

def score_v1_keyword_title(title, config):
    """Return bounded score and matched V1 cluster IDs; neutral if no match."""
    if not isinstance(title,str) or not isinstance(config,dict) or not isinstance(config.get("clusters"),list):
        raise ValueError("invalid_keyword_scoring_input")
    normalized=" ".join(title.casefold().split())
    hits=[]
    weights=[]
    for cluster in config["clusters"]:
        if not isinstance(cluster,dict):
            raise ValueError("invalid_keyword_cluster")
        terms=cluster.get("phrases",[])+cluster.get("tags",[])
        if not isinstance(terms,list):
            raise ValueError("invalid_keyword_terms")
        matched=False
        for term in terms:
            if not isinstance(term,str) or not term.strip():
                continue
            needle=" ".join(term.casefold().split())
            if re.search(r"(?<!\w)"+re.escape(needle)+r"(?!\w)",normalized):
                matched=True
                break
        if matched:
            hits.append(str(cluster.get("id","unknown")))
            weights.append(WEIGHTS.get(cluster.get("prio"),6))
    return min(100,50+max(weights,default=0)+min(12,max(0,len(hits)-1)*3)),hits

def score_keyword_context(title, lead, config):
    """Additive keyword evidence from a bounded article lead; preserve title hits."""
    if not isinstance(lead,str):
        raise ValueError("invalid_keyword_context")
    title_score,title_hits=score_v1_keyword_title(title,config)
    combined_score,combined_hits=score_v1_keyword_title(title+" "+lead[:1200],config)
    return max(title_score,combined_score),list(dict.fromkeys(title_hits+combined_hits))
