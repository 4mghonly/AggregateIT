"""Offline B126 evidence auditor; never authorizes publication."""
import argparse,json
from pathlib import Path
from v2_b126_weekly_editorial_audit import audit

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--paired-json",required=True)
    p.add_argument("--b125-json",required=True)
    p.add_argument("--candidate-sha",required=True)
    p.add_argument("--output",default="b126_weekly_editorial_audit.json")
    a=p.parse_args()
    pairs=json.loads(Path(a.paired_json).read_text(encoding="utf8"))
    b125=json.loads(Path(a.b125_json).read_text(encoding="utf8"))
    result=audit(pairs,b125,expected_sha=a.candidate_sha)
    Path(a.output).write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf8")
    print(json.dumps({"source_roster_seven_days":result["source_roster_seven_days"],
                      "selection_disagreements_observed":result["selection_disagreements_observed"],
                      "issues":result["issues"],"release":"HOLD"}))
    return 0 if result["source_roster_seven_days"] else 2
if __name__=="__main__":
    raise SystemExit(main())
