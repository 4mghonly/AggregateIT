"""Offline B127 identity-matched editorial review builder. No model, delivery, or network."""
import argparse,json
from pathlib import Path
from v2_b127_identity_review import build_queue

def load(path):
    raw=Path(path).read_bytes()
    if len(raw)>2_000_000:
        raise ValueError("unbounded_input")
    return json.loads(raw)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--reviews-json",required=True)
    parser.add_argument("--rosters-json",required=True)
    parser.add_argument("--b126-json",required=True)
    parser.add_argument("--candidate-sha",required=True)
    parser.add_argument("--output",default="b127_identity_review.json")
    args=parser.parse_args()
    result=build_queue(load(args.reviews_json),load(args.rosters_json),
                       load(args.b126_json),expected_sha=args.candidate_sha)
    Path(args.output).write_text(json.dumps(result,indent=2,sort_keys=True,ensure_ascii=False)+"\n",encoding="utf8")
    print(json.dumps({"evidence_reconciled":result["evidence_reconciled"],
                      "disagreement_count":result["disagreement_count"],
                      "counts":result["counts"],"issues":result["issues"],
                      "review_status":result["review_status"],"release":"HOLD"}))
    return 0 if result["evidence_reconciled"] else 2
if __name__=="__main__":
    raise SystemExit(main())
