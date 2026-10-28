"""B95-97: bounded, authenticated-by-digest historical receipt consolidation.

Only local artifact receipts supplied by operator/CI are ingested. This is not
a GitHub API client, nor a claim that publisher feeds are redundant.
"""
from __future__ import annotations
import json,re
from datetime import date,timedelta
from hashlib import sha256
from pathlib import Path
from v2_editorial import AR_REGIONS

def consolidate(directory:Path,*,today:date)->dict:
 root=Path(directory)
 receipts=[]
 if root.exists():
  files=sorted(root.glob("*.json"))
  if len(files)>60:raise ValueError("history_file_limit")
  for file in files:
   if file.is_symlink() or file.stat().st_size>65536:raise ValueError("unsafe_history_file")
   raw=file.read_bytes()
   obj=json.loads(raw)
   if obj.get("schema")!="aggregateit-v2-b95-daily-history/1" or obj.get("can_release") is not False:raise ValueError("untrusted_history_receipt")
   day=obj.get("day")
   if not isinstance(day,str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}",day):raise ValueError("invalid_history_day")
   when=date.fromisoformat(day)
   if when>today or when<today-timedelta(days=29):raise ValueError("out_of_retention")
   counts=obj.get("stories")
   if not isinstance(counts,dict) or set(counts)!={"english","arabic"} or any(type(v)!=int or not 0<=v<=30 for v in counts.values()):raise ValueError("invalid_story_counts")
   digest=obj.get("evidence_sha256")
   if not isinstance(digest,str) or not re.fullmatch("[0-9a-f]{64}",digest):raise ValueError("missing_evidence_digest")
   receipts.append((day,counts,digest))
 # Duplicates on the same day must agree, otherwise abstain rather than cherry-pick.
 unique={}
 for day,counts,digest in receipts:
  if day in unique and unique[day]!=(counts,digest):raise ValueError("conflicting_same_day_evidence")
  unique[day]=(counts,digest)
 window={day:counts for day,(counts,_) in unique.items() if date.fromisoformat(day)>=today-timedelta(days=6)}
 eligible={lang:sum(counts[lang]>0 for counts in window.values()) for lang in ("english","arabic")}
 return {"schema":"aggregateit-v2-b95-b97-history/1","unique_days":len(unique),"last_seven_days":eligible,"seven_day_evidence_met":all(v==7 for v in eligible.values()),"publisher_redundancy_verified":False,"can_release":False}

def make_daily(acceptance:dict,*,day:str)->dict:
 if acceptance.get("schema")!="aggregateit-v2-b88-b90-acceptance/1" or acceptance.get("can_release") is not False:raise ValueError("untrusted_acceptance")
 counts={lang:acceptance["b89_source_coverage"][lang]["selected_stories"] for lang in ("english","arabic")}
 if any(type(v)!=int or not 0<=v<=30 for v in counts.values()):raise ValueError("invalid_counts")
 date.fromisoformat(day)
 digest=sha256(json.dumps(acceptance,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
 return {"schema":"aggregateit-v2-b95-daily-history/1","day":day,"stories":counts,"evidence_sha256":digest,"can_release":False}

def main():
 from datetime import datetime,timezone
 today=datetime.now(timezone.utc).date()
 a=json.loads(Path("b88_b90_acceptance.json").read_text())
 out=Path("b95-history");out.mkdir(exist_ok=True)
 receipt=make_daily(a,day=today.isoformat())
 (out/(today.isoformat()+".json")).write_text(json.dumps(receipt,sort_keys=True)+"\n")
 result=consolidate(out,today=today)
 result["arabic_target_regions"]=len(AR_REGIONS)
 result["source_expansion_status"]="HOLD_NO_ADDITIONAL_PUBLISHER_VALIDATED"
 Path("b95_b97_history.json").write_text(json.dumps(result,indent=2)+"\n")
 print(json.dumps(result))
if __name__=="__main__":main()
