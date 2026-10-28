"""B94: truthful daily no-post evidence accumulation in bounded SQLite."""
from __future__ import annotations
import json,sqlite3
from pathlib import Path
from datetime import date,datetime,timezone,timedelta

def record(db:Path,acceptance:dict,*,observed_at:str)->dict:
 if acceptance.get("schema")!="aggregateit-v2-b88-b90-acceptance/1" or acceptance.get("can_release") is not False:raise ValueError("untrusted_acceptance")
 try:stamp=datetime.fromisoformat(observed_at.replace("Z","+00:00"))
 except (TypeError,ValueError):raise ValueError("invalid_observation_time") from None
 if stamp.tzinfo is None or stamp.utcoffset() is None:raise ValueError("naive_observation")
 if abs((datetime.now(timezone.utc)-stamp.astimezone(timezone.utc)).total_seconds())>86400:raise ValueError("observation_outside_one_day")
 products=acceptance.get("b89_source_coverage")
 if not isinstance(products,dict) or set(products)!={"english","arabic"}:raise ValueError("missing_bilingual_coverage")
 counts={}
 for lang in ("english","arabic"):
  n=products[lang].get("selected_stories")
  if type(n) is not int or not 0<=n<=30:raise ValueError("invalid_selected_story_count")
  counts[lang]=n
 db=Path(db);db.parent.mkdir(parents=True,exist_ok=True)
 with sqlite3.connect(db) as conn:
  conn.execute("CREATE TABLE IF NOT EXISTS daily_receipts (day TEXT NOT NULL, lang TEXT NOT NULL, stories INTEGER NOT NULL, observed_at TEXT NOT NULL, PRIMARY KEY(day,lang))")
  day=stamp.astimezone(timezone.utc).date().isoformat()
  for lang,n in counts.items():
   # Same-day reruns update one daily slot; never inflate the seven-day count.
   conn.execute("INSERT INTO daily_receipts(day,lang,stories,observed_at) VALUES(?,?,?,?) ON CONFLICT(day,lang) DO UPDATE SET stories=excluded.stories,observed_at=excluded.observed_at",(day,lang,n,stamp.isoformat()))
  cutoff=(datetime.now(timezone.utc).date()-timedelta(days=30)).isoformat()
  conn.execute("DELETE FROM daily_receipts WHERE day<?",(cutoff,))
  rows=conn.execute("SELECT lang,COUNT(*) FROM daily_receipts WHERE stories>0 AND day>=? GROUP BY lang",((datetime.now(timezone.utc).date()-timedelta(days=6)).isoformat(),)).fetchall()
 days=dict(rows)
 return {"schema":"aggregateit-v2-b94-daily-evidence/1","window_days":7,"distinct_days_with_stories":{x:days.get(x,0) for x in ("english","arabic")},"seven_day_evidence_met":all(days.get(x,0)>=7 for x in ("english","arabic")),"can_release":False,"discord_sent":False}

def main():
 a=json.loads(Path("b88_b90_acceptance.json").read_text())
 report=record(Path("b94-daily-evidence.sqlite"),a,observed_at=datetime.now(timezone.utc).isoformat())
 Path("b94_daily_evidence.json").write_text(json.dumps(report,indent=2)+"\n")
 print(json.dumps(report))
if __name__=="__main__":main()
