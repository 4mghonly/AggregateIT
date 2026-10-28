"""Persist sanitized B46 run receipts in isolated SQLite; no article text/HTML."""
import hashlib,json
from pathlib import Path
from v2_sqlite_store import Store

def save_receipt(result,path):
    if result.get("schema")!="aggregateit-v2-b46-live-chain/1":raise ValueError("invalid_receipt_schema")
    if result.get("discord_sent") is not False or result.get("can_release") is not False:raise ValueError("unsafe_release_receipt")
    observed=result["observed_at"]
    identity=hashlib.sha256((observed+json.dumps(result.get("rss_feed_sha256",{}),sort_keys=True)).encode()).hexdigest()
    with Store(path) as db:
        for product,language in (("english","en"),("arabic","ar")):
            source=result["source_attempts"][product]
            db.put("source_health",language,identity,{"feed_ok":source["feed_ok"],"article_attempts":source["article_attempts"],"article_http_ok":source["article_http_ok"],"eligible":source["article_evidence_eligible"]},observed_at=observed)
            db.put("edition_evidence",language,identity,{"story_count":result["editorial"]["products"][product]["story_count"],"native_status":result["native"]["status"],"release":False},observed_at=observed)
        db.cleanup()
        return {"db_bytes":db.size_bytes(),"source_health":db.count("source_health"),"edition_evidence":db.count("edition_evidence"),"article_rows":db.count("articles"),"identity":identity}
