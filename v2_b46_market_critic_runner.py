"""B46 bounded one-shot public scanner: zero secrets, no article source upload."""
import json
from pathlib import Path
from datetime import datetime, timezone
from v2_b46_market_analytics import assess_market_observation,MACRO
from v2_b46_live_editorial import compile_captured_articles
from v2_b46_market_analytics import audit_critic_abstention

def run():
    now=datetime.now(timezone.utc).isoformat()
    # Minimal optional data collection: single POST, no retries, no screenshots,
    # and no price values persisted or used by either product.
    market={"status":"UNAVAILABLE","failure_class":None}
    try:
        import requests
        url="https://scanner.tradingview.com/global/scan"
        body={"symbols":{"tickers":list(MACRO)},"columns":["description","change","close"],"options":{"lang":"en"}}
        result=requests.post(url,json=body,timeout=8,allow_redirects=False,
                             headers={"Accept":"application/json","User-Agent":"AggregateIT-V2-Research/1.0"},
                             stream=True)
        if result.status_code!=200:
            market["failure_class"]="http_"+str(result.status_code)
        else:
            limit=200000
            payload=bytearray()
            for chunk in result.iter_content(chunk_size=32768):
                payload.extend(chunk)
                if len(payload)>limit:raise ValueError("scanner_response_over_budget")
            obj=json.loads(bytes(payload))
            check=assess_market_observation(obj,observed_at=now)
            market={"status":"OBSERVED_UNVERIFIED","data":check}
        result.close()
    except Exception as exc:
        market["failure_class"]=type(exc).__name__
    editorial=compile_captured_articles([],as_of=now,slot_id=now)
    critical=audit_critic_abstention(editorial["products"])
    return {"schema":"aggregateit-v2-b46-macro-critic-no-post/1",
        "market":market,"naysayer":critical,
        "live_tradingview_post_attempted":True,
        "exchange_timestamp_verified":False,"no_quote_values_persisted":True,
        "market_data_published":False,
        "model_called":False,"discord_sent":False,"can_release":False}
if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser();p.add_argument("--output",type=Path,required=True)
    args=p.parse_args();data=run()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print(json.dumps({"market_status":data["market"]["status"],
                      "failure_class":data["market"].get("failure_class"),
                      "received":data["market"].get("data",{}).get("received_count",0),
                      "naysayer":{k:v["review_status"] for k,v in data["naysayer"]["products"].items()},
                      "can_release":False}))
