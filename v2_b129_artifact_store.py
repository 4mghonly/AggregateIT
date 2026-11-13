"""B129 local-only immutable generated product artifact store.

Caller supplies its own generated HTML/PDF/editorial JSON; never fetches publisher
pages or persists source article bodies by itself. No production integration.
"""
from pathlib import Path
from hashlib import sha256
import json,os,shutil,tempfile
from v2_b129_daily_product_archive import make_snapshot
KINDS=("html","pdf","json")
NAMES=("daily.html","daily.pdf","editorial.json")
LIMITS=(2_000_000,15_000_000,2_000_000)

def store_day(root,*,utc_date,head_sha,run_id,capture_sha256,source_files,story_identities):
 root=Path(root)
 if not isinstance(source_files,dict) or set(source_files)!=set(("english","arabic")):
  raise ValueError("missing_bilingual_files")
 if not isinstance(story_identities,dict) or set(story_identities)!=set(source_files):
  raise ValueError("missing_bilingual_story_identities")
 payloads={}
 for product,files in source_files.items():
  if not isinstance(files,(tuple,list)) or len(files)!=3:
   raise ValueError("three_files_required")
  data=[]
  for f,limit in zip(files,LIMITS):
   path=Path(f)
   if not path.is_file() or path.is_symlink() or path.stat().st_size<=0 or path.stat().st_size>limit:
    raise ValueError("missing_or_unbounded_generated_artifact")
   data.append(path.read_bytes())
  if not data[0].lstrip().lower().startswith((b"<!doctype html",b"<html")) or not data[1].startswith(b"%PDF-") or not isinstance(json.loads(data[2]),dict):
   raise ValueError("invalid_generated_artifact_type")
  payloads[product]=data
 products={}
 for p,data in payloads.items():
  products[p]={"daily_html_sha256":sha256(data[0]).hexdigest(),
    "daily_pdf_sha256":sha256(data[1]).hexdigest(),
    "editorial_payload_sha256":sha256(data[2]).hexdigest(),
    "story_identities":story_identities[p],"market_data_evidence":"NOT_VERIFIED",
    "translation_evidence":"NOT_VERIFIED","publisher_rights":"UNVERIFIED","rendered":True}
 receipt=make_snapshot(utc_date=utc_date,head_sha=head_sha,run_id=run_id,
                       capture_sha256=capture_sha256,products=products)
 target=root/utc_date
 if target.exists():raise FileExistsError(str(target))
 root.mkdir(parents=True,exist_ok=True)
 stage=Path(tempfile.mkdtemp(prefix=".b129-",dir=root))
 try:
  for p,data in payloads.items():
   directory=stage/p
   directory.mkdir()
   for name,blob in zip(NAMES,data):
    (directory/name).write_bytes(blob)
  (stage/"manifest.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf8")
  # Do not overwrite an existing day. Single-writer expected; concurrent writes
  # must be externally serialized, since a directory rename may replace an empty directory.
  if target.exists():raise FileExistsError(str(target))
  stage.rename(target)
 except BaseException:
  if stage.exists():shutil.rmtree(stage)
  raise
 return receipt

def verify_stored_day(directory):
 directory=Path(directory)
 receipt=json.loads((directory/"manifest.json").read_text(encoding="utf8"))
 for product in ("english","arabic"):
  for name,key in zip(NAMES,("daily_html_sha256","daily_pdf_sha256","editorial_payload_sha256")):
   file=directory/product/name
   if file.is_symlink() or sha256(file.read_bytes()).hexdigest()!=receipt["products"][product][key]:
    raise ValueError("artifact_digest_mismatch")
 return receipt
