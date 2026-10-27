"""B43: genuine four-candidate qualification through unchanged production audit.

Each static publisher gets one website and one feed request from the actual
arabic_source_audit.probe. Captures feed response only in RAM to exercise
the real Arabic collector, translation validation/routing and duplicate logic.
No send, no model call, no source activation or external artifact content.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from difflib import SequenceMatcher
from hashlib import sha256
import json
import re
from pathlib import Path
from unittest.mock import patch
from urllib.parse import urlsplit

import arabic_source_audit as production_audit
from arabic_newsletter import collect as production_collect
from arabic_newsletter.core import canonical
from arabic_live_v2 import _dedupe_key, _normalize_translations, _source_is_arabic
from langdetect import DetectorFactory, detect_langs
import requests

DetectorFactory.seed = 0
_CANDIDATES = (
 {"id":"candidate-shabelle","name":"Shabelle Media Network","family":"shabelle",
  "website":"https://shabellemedia.com","feed":"https://shabellemedia.com/feed/",
  "language":"so","region":"somalia","country":"SO","affiliation":"unverified"},
 {"id":"candidate-puntland-post","name":"Puntland Post","family":"puntland_post",
  "website":"https://puntlandpost.net","feed":"https://puntlandpost.net/feed/",
  "language":"so","region":"somalia","country":"SO","affiliation":"unverified"},
 {"id":"candidate-somali-dispatch","name":"Somali Dispatch","family":"somali_dispatch",
  "website":"https://www.somalidispatch.com","feed":"https://www.somalidispatch.com/feed/",
  "language":"en","region":"somalia","country":"SO","affiliation":"unverified"},
 {"id":"candidate-goobjoog-en","name":"Goobjoog English","family":"goobjoog",
  "website":"https://en.goobjoog.com","feed":"https://en.goobjoog.com/feed/",
  "language":"en","region":"somalia","country":"SO","affiliation":"unverified"},
)
MAX_FEED_BYTES=1_000_000

def validate_candidate(row):
    if not isinstance(row,dict) or row.get("region")!="somalia" or row.get("country")!="SO":
        raise ValueError("unapproved_candidate")
    if row.get("enabled",False) is not False:
        raise ValueError("candidate_must_remain_disabled")
    for key in ("website","feed"):
        p=urlsplit(row[key])
        if p.scheme!="https" or not p.hostname or p.username or p.password or p.port not in (None,443):
            raise ValueError("insecure_candidate_url")
    if row["language"] not in ("so","en","ar"):
        raise ValueError("unapproved_candidate_language")
    return row

def audit_one(row, *, audited_probe=None, request_get=None):
    """Run the actual production validator; trace the exact feed response bytes."""
    row=validate_candidate(row)
    actual_get=request_get or requests.get
    feed_body={}
    count=Counter()
    def capture(url,*args,**kwargs):
        count[str(url)]+=1
        if url not in (row["feed"],row["website"]):
            raise ValueError("unexpected_source_request")
        response=actual_get(url,*args,**kwargs)
        if url==row["feed"] and response.status_code==200:
            raw=response.content
            if len(raw)>MAX_FEED_BYTES:
                raise ValueError("unbounded_feed")
            feed_body["raw"]=raw
        return response
    with patch.object(production_audit.requests,"get",side_effect=capture):
        audit=(audited_probe or production_audit.probe)(row)
    if not isinstance(audit,dict) or audit.get("id")!=row["id"]:
        raise ValueError("production_audit_identity_mismatch")
    raw=feed_body.get("raw")
    if raw is None:
        return audit,None,{"requests":dict(count),"captured":False}
    return audit,raw,{"requests":dict(count),"captured":True,
                      "feed_sha256":sha256(raw).hexdigest(),"bytes":len(raw)}

def collector_same_bytes(row:dict, raw:bytes)->tuple[list[dict],dict]:
    if not isinstance(raw,bytes) or len(raw)>MAX_FEED_BYTES:
        raise ValueError("invalid_same_bytes")
    def feed_only(url):
        if url!=row["feed"]:
            raise production_collect.FetchError("no_extra_network_for_replay")
        return raw
    with patch.object(production_collect,"fetch",side_effect=feed_only):
        return production_collect.collect_source(row,discover=False)

def language_route(items:list[dict],*,declared_language:str)->dict:
    if declared_language not in ("en","so","ar"):
        raise ValueError("invalid_language")
    titles=[x.get("title","") for x in items[:12] if isinstance(x.get("title"),str)]
    corpus=" ".join(titles)
    detection=None; confidence=None
    if len(corpus)>=80:
        try:
            results=detect_langs(corpus[:2500])
            if results:
                detection=results[0].lang
                confidence=round(float(results[0].prob),4)
        except Exception:
            pass
    foreign=sum(not _source_is_arabic(x) for x in items)
    mismatch=(detection in ("en","so","ar") and detection!=declared_language and
              confidence is not None and confidence>=0.9)
    # Predictions are heuristics; never silently rewrite source metadata.
    return {"declared_language":declared_language,
            "aggregated_headline_language_guess":detection,
            "language_guess_confidence":confidence,
            "declared_language_mismatch_suspected":bool(mismatch),
            "untranslated_items_requiring_arabic":foreign,
            "model_translation_performed":False,
            "metadata_language_auto_corrected":False,
            "language_verified_by_human_or_publisher":False}

def translation_contract():
    """Exercise the *production* Arabic translation verifier, not a model."""
    original={"language":"en","title":"Somalia officials met on 27 October",
              "summary":"The meeting involved 12 delegates.","source":"synthetic_fixture"}
    good={"items":[{"index":0,"title_ar":"اجتمع مسؤولون صوماليون يوم 27 أكتوبر",
                    "summary_ar":"ضم الاجتماع 12 مندوباً."}]}
    wrong={"items":[{"index":0,"title_ar":"اجتمع مسؤولون صوماليون يوم 27 أكتوبر",
                     "summary_ar":"ضم الاجتماع 13 مندوباً."}]}
    nonarabic={"items":[{"index":0,"title_ar":original["title"],
                          "summary_ar":original["summary"]}]}
    return {"production_normalizer_accepts_valid_arabic_with_numbers":
                bool(_normalize_translations(good,[original])),
            "rejects_number_mutation":not bool(_normalize_translations(wrong,[original])),
            "rejects_non_arabic_output":not bool(_normalize_translations(nonarabic,[original])),
            "actual_model_called":False,"live_translation_accuracy_measured":False,
            "primary_fallback_connectivity_tested":False}

def dedupe_stats(items_by_source:dict[str,list[dict]],*,now:datetime)->dict:
    if now.utcoffset() is None:raise ValueError("timezone_required")
    rows=[]
    for family,items in items_by_source.items():
        for item in items[:35]:
            when=item.get("published")
            if not isinstance(when,(float,int)) or isinstance(when,bool):
                continue
            age=now.timestamp()-when
            if not 0<=age<=259200:continue
            title=item.get("title")
            if not isinstance(title,str) or not title:continue
            key=_dedupe_key(title)
            if not key:continue
            url=canonical(item["url"]) if item.get("url") else None
            rows.append((family,url,key,float(when)))
    pairs=0;url_pairs=0;title_pairs=0;cross_pairs=0;families=set()
    for i,(family,url,title,_) in enumerate(rows):
        for other_family,other_url,other_title,_ in rows[i+1:]:
            url_match=(url is not None and url==other_url)
            title_match=(title==other_title or (min(len(title),len(other_title))>=20 and
                         SequenceMatcher(None,title,other_title).ratio()>=0.94))
            if url_match or title_match:
                pairs+=1
                url_pairs+=bool(url_match)
                title_pairs+=bool(title_match)
                if family!=other_family:
                    cross_pairs+=1;families.update([family,other_family])
    return {"recent_items_compared":len(rows),"duplicated_pairs":pairs,
            "identical_link_pairs":url_pairs,"near_identical_title_pairs":title_pairs,
            "cross_publisher_duplicate_pairs":cross_pairs,
            "publisher_families_in_cross_duplicates":len(families),
            "cross_language_paraphrase_duplicates_covered":False,
            "semantic_event_equivalence_proven":False,"headline_text_persisted":False}

def run():
    now=datetime.now(timezone.utc)
    reports=[]; items_by_source={}
    for base in _CANDIDATES:
        row=validate_candidate({**base,"enabled":False})
        audit,raw,transport=audit_one(row)
        rec={"candidate_id":row["id"],"publisher_family":row["family"],
             "feed_url":row["feed"],"declared_language":row["language"],
             "production_validator":"arabic_source_audit.probe (unchanged)",
             "website_ok":audit.get("website_ok"),"website_http":audit.get("website_http"),
             "feed_http":audit.get("feed_http"),
             "production_compatible":audit.get("production_compatible") is True,
             "production_reason":audit.get("reason"),
             "production_feed_entries":audit.get("entries",0),
             "production_recent_72h":audit.get("recent_72h",0),
             "production_feed_bozo":audit.get("bozo"),
             "feed_sha256":transport.get("feed_sha256"),
             "retrieved_body_available":bool(raw)}
        if raw is not None:
            items,health=collector_same_bytes(row,raw)
            items_by_source[row["family"]]=items
            rec["collector_status"]=health.get("status")
            rec["collector_items"]=len(items)
            rec["collector_dated_items"]=health.get("dated_items")
            rec["collector_recent_72h"]=sum(x.get("published") is not None
                                and 0<=now.timestamp()-x["published"]<=259200 for x in items)
            rec["translation_route"]=language_route(items,declared_language=row["language"])
        else:
            rec["collector_status"]="no_cached_feed"
            rec["collector_items"]=0
            rec["collector_recent_72h"]=0
            rec["translation_route"]=language_route([],declared_language=row["language"])
        rec["eligible_for_disabled_v2_staging"]=(rec["production_compatible"] and
               rec["collector_recent_72h"]>=1 and rec["collector_items"]>=1 and
               not rec["translation_route"]["declared_language_mismatch_suspected"])
        rec["enabled"]=False
        rec["production_promoted"]=False
        reports.append(rec)
    dup=dedupe_stats(items_by_source,now=now)
    contract=translation_contract()
    if not all(contract[k] for k in ("production_normalizer_accepts_valid_arabic_with_numbers",
                                      "rejects_number_mutation","rejects_non_arabic_output")):
        raise RuntimeError("translation_validation_contract_regressed")
    return {"schema":"aggregateit-v2-b43-somalia-candidate-validation/1",
            "observed_at":now.isoformat(),"candidate_count":len(reports),
            "results":reports,"translation_contract":contract,"duplication":dup,
            "production_compatible_count":sum(x["production_compatible"] for x in reports),
            "disabled_staging_eligible_count":sum(x["eligible_for_disabled_v2_staging"] for x in reports),
            "live_model_translation_proven":False,
            "production_sources_changed":False,"new_sources_enabled":False,
            "database_modified":False,"discord_sent":False,"can_release":False}

def main():
    from argparse import ArgumentParser
    ap=ArgumentParser();ap.add_argument("--output",required=True)
    args=ap.parse_args()
    data=run()
    outfile=Path(args.output);outfile.parent.mkdir(parents=True,exist_ok=True)
    outfile.write_text(json.dumps(data,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
    print(json.dumps({"candidate_count":data["candidate_count"],
      "validation":[{"id":x["candidate_id"],"pass":x["production_compatible"],
                     "entries":x["production_feed_entries"],
                     "recent":x["production_recent_72h"],
                     "collector":x["collector_status"],
                     "detected":x["translation_route"]["aggregated_headline_language_guess"],
                     "metadata_mismatch":x["translation_route"]["declared_language_mismatch_suspected"]}
                    for x in data["results"]],
      "duplication":data["duplication"],
      "translation_contract":data["translation_contract"]},ensure_ascii=False))
if __name__=="__main__":main()
