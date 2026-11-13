"""Offline B125 acceptance entrypoint; input run metadata must be independently fetched from GitHub.

No network, database, publisher, model, Discord or production calls.
"""
import argparse
import json
from pathlib import Path
from v2_b125_evidence_reconciliation import reconcile

def load(path):
    data=json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data,list) or len(data)>45:
        raise ValueError("expected_bounded_json_array")
    return data

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--pairs",required=True)
    parser.add_argument("--rosters",required=True)
    parser.add_argument("--github-runs",required=True)
    parser.add_argument("--candidate-sha",required=True)
    parser.add_argument("--output",default="b125_evidence_reconciliation.json")
    args=parser.parse_args()
    result=reconcile(load(args.pairs),load(args.rosters),load(args.github_runs),
                     expected_sha=args.candidate_sha)
    Path(args.output).write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"seven_verified":result["seven_verified"],
                      "verified_dates":result["verified_dates"],
                      "issues":result["issues"],"release":"HOLD"}))
    return 0 if result["seven_verified"] else 2

if __name__=="__main__":
    raise SystemExit(main())
