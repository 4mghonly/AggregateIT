"""Offline B128 independent editorial-review readiness and weekly scope assessment."""
import argparse,json
from pathlib import Path
from v2_b128_adjudication import assess
def load(path):
    raw=Path(path).read_bytes()
    if len(raw)>2_000_000:raise ValueError("unbounded_evidence")
    return json.loads(raw)
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--b127",required=True)
    p.add_argument("--b126",required=True)
    p.add_argument("--candidate-sha",required=True)
    p.add_argument("--output",default="b128_adjudication_readiness.json")
    a=p.parse_args()
    result=assess(load(a.b127),load(a.b126),expected_sha=a.candidate_sha)
    Path(a.output).write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf8")
    print(json.dumps({"review_queue_valid":result["review_queue_valid"],"pending":result["pending_count"],"triage":result["triage"],"issues":result["issues"],"release":"HOLD"}))
    return 0 if result["review_queue_valid"] else 2
if __name__=="__main__":
    raise SystemExit(main())
