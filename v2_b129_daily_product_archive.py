"""B129 no-post daily analytical-product evidence manifest and weekly verifier.

Manifest records cryptographic pointers, not copyrighted article bodies or proof
of editorial, model, visual, translation, rights or delivery parity.
"""
import json,re
from hashlib import sha256
from datetime import date,timedelta
HEX64=re.compile(r"[0-9a-f]{64}\Z")
HEX40=re.compile(r"[0-9a-f]{40}\Z")
RUN=re.compile(r"[1-9][0-9]{0,17}\Z")
SCHEMA="aggregateit-v2-b129-daily-product-evidence/1"
WEEK="aggregateit-v2-b129-seven-day-product-evidence/1"
FIELDS={"daily_html_sha256","daily_pdf_sha256","editorial_payload_sha256",
        "story_identities","market_data_evidence","translation_evidence",
        "publisher_rights","rendered"}
def digest(data):
 return sha256(json.dumps(data,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()
def validhex(x,n=64):
 return isinstance(x,str) and bool((HEX64 if n==64 else HEX40).fullmatch(x))
def make_snapshot(*,utc_date,head_sha,run_id,capture_sha256,products):
 try:date.fromisoformat(utc_date)
 except (ValueError,TypeError):raise ValueError("invalid_utc_date") from None
 if not validhex(head_sha,40) or not isinstance(run_id,str) or not RUN.fullmatch(run_id) or not validhex(capture_sha256):
  raise ValueError("invalid_provenance")
 if not isinstance(products,dict) or set(products)!={"english","arabic"}:raise ValueError("missing_bilingual_product")
 safe={}
 for lang,item in products.items():
  if not isinstance(item,dict) or set(item)!=FIELDS:raise ValueError("unapproved_product_fields")
  if not all(validhex(item.get(k)) for k in ("daily_html_sha256","daily_pdf_sha256","editorial_payload_sha256")):
   raise ValueError("missing_payload_digest")
  ids=item["story_identities"]
  if not isinstance(ids,list) or not 0<len(ids)<=30 or any(not validhex(v) for v in ids) or len(set(ids))!=len(ids):
   raise ValueError("invalid_story_identities")
  if (item["rendered"] is not True or item["market_data_evidence"]!="NOT_VERIFIED" or
      item["translation_evidence"]!="NOT_VERIFIED" or item["publisher_rights"]!="UNVERIFIED"):
   raise ValueError("unsupported_acceptance_claim")
  safe[lang]={**item,"story_identities":list(ids)}
 result={"schema":SCHEMA,"utc_date":utc_date,"head_sha":head_sha,
         "github_run_id":run_id,"capture_sha256":capture_sha256,"products":safe,
         "original_publisher_text_persisted":False,"can_release":False}
 result["manifest_sha256"]=digest(result)
 return result

def verify_week(rows,*,expected_sha):
 issues=[]
 if not isinstance(rows,list) or len(rows)!=7:issues.append("require_exactly_seven_snapshots")
 if not validhex(expected_sha,40):issues.append("invalid_candidate")
 days=[]
 seen=set()
 for row in rows if isinstance(rows,list) else []:
  if not isinstance(row,dict):
   issues.append("invalid_receipt");continue
  value=dict(row);receipt_hash=value.pop("manifest_sha256",None)
  if (row.get("schema")!=SCHEMA or row.get("can_release") is not False or
      receipt_hash!=digest(value) or row.get("head_sha")!=expected_sha or
      row.get("original_publisher_text_persisted") is not False):
   issues.append("receipt_integrity_failure")
  day=row.get("utc_date")
  try:parsed=date.fromisoformat(day)
  except (ValueError,TypeError):issues.append("invalid_date");continue
  if day in seen:issues.append("duplicate_date")
  seen.add(day);days.append(parsed)
  if not isinstance(row.get("products"),dict) or set(row["products"])!={"english","arabic"}:
   issues.append("missing_product")
  else:
   try:make_snapshot(utc_date=day,head_sha=row["head_sha"],
        run_id=row["github_run_id"],capture_sha256=row["capture_sha256"],
        products=row["products"])
   except (ValueError,KeyError,TypeError):issues.append("invalid_product_evidence")
 if len(days)==7 and len(set(days))==7:
  ordered=sorted(days)
  if any(ordered[i+1]-ordered[i]!=timedelta(days=1) for i in range(6)):
   issues.append("nonconsecutive_dates")
 else:issues.append("incomplete_week")
 return {"schema":WEEK,"candidate_sha":expected_sha,
         "seven_daily_snapshots_verified":not issues,
         "verified_dates":sorted(set(d.isoformat() for d in days)),
         "full_weekly_product_parity_verified":False,
         "independent_editorial_model_translation_visual_delivery_rights_verified":False,
         "can_release":False,"issues":sorted(set(issues))}
