"""B129 no-network manifest verifier. Input: seven original daily product manifests."""
import argparse,json
from pathlib import Path
from v2_b129_daily_product_archive import verify_week

def main():
 p=argparse.ArgumentParser()
 p.add_argument("--manifest-dir",required=True)
 p.add_argument("--candidate-sha",required=True)
 p.add_argument("--output",default="b129_weekly_product_evidence.json")
 a=p.parse_args()
 root=Path(a.manifest_dir)
 if not root.is_dir():p.error("manifest directory not found")
 files=sorted(root.glob("*.json"))
 if len(files)>14:p.error("unbounded manifest directory")
 rows=[]
 for path in files:
  if path.is_symlink() or path.stat().st_size>128000:p.error("invalid manifest file")
  rows.append(json.loads(path.read_text(encoding="utf8")))
 result=verify_week(rows,expected_sha=a.candidate_sha)
 Path(a.output).write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf8")
 print(json.dumps({"seven_daily_snapshots_verified":result["seven_daily_snapshots_verified"],
                   "issues":result["issues"],"release":"HOLD"}))
 return 0 if result["seven_daily_snapshots_verified"] else 2
if __name__=="__main__":
 raise SystemExit(main())
