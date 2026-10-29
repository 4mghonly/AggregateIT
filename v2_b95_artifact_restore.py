"""Restore bounded B95 daily receipts from prior successful GitHub Actions artifacts.

Uses the runner's read-only GITHUB_TOKEN, not Drive or production credentials.
Failures leave the evidence gate closed. Only matching branch/workflow artifacts
are eligible. Never downloads or restores a database.
"""
from __future__ import annotations
import json,os,subprocess,zipfile
from pathlib import Path
from datetime import date,timedelta

WORKFLOW="v2-b80-b83-live-acceptance.yml"
ARTIFACT="aggregateit-v2-b80-b83-real-acceptance"
BRANCH="rebuild/aggregateit-v2"

def restore(directory:Path,*,today:date,repo:str,token:str)->dict:
 if not token or not repo or "/" not in repo:raise ValueError("missing_readonly_github_credentials")
 directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
 import urllib.request
 def get(url):
  req=urllib.request.Request(url,headers={"Authorization":"Bearer "+token,"Accept":"application/vnd.github+json","X-GitHub-Api-Version":"2022-11-28"},method="GET")
  with urllib.request.urlopen(req,timeout=12) as response:return json.load(response)
 from urllib.parse import quote
 url=f"https://api.github.com/repos/{repo}/actions/workflows/{WORKFLOW}/runs?branch={quote(BRANCH)}&status=success&per_page=35"
 runs=get(url).get("workflow_runs",[])
 restored=0
 for run in runs:
  if restored>=12:break
  if run.get("head_branch")!=BRANCH or run.get("conclusion")!="success":continue
  run_id=run.get("id")
  if type(run_id) is not int:continue
  artifacts=get(f"https://api.github.com/repos/{repo}/actions/runs/{run_id}/artifacts").get("artifacts",[])
  for a in artifacts:
   if a.get("name")!=ARTIFACT or a.get("expired") or not isinstance(a.get("size_in_bytes"),int) or a["size_in_bytes"]>35_000_000:continue
   # GitHub's artifact endpoint redirects to a temporary signed URL.
   req=urllib.request.Request(a["archive_download_url"],headers={"Authorization":"Bearer "+token,"Accept":"application/vnd.github+json"})
   import io
   class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,request,fp,code,msg,headers,newurl):return None
   opener=urllib.request.build_opener(NoRedirect)
   try:
    opener.open(req,timeout=25)
    raise ValueError('missing_artifact_redirect')
   except urllib.error.HTTPError as exc:
    if exc.code not in (302,307):raise
    signed=exc.headers.get('Location','')
   from urllib.parse import urlsplit
   target=urlsplit(signed)
   if target.scheme!='https' or not target.hostname or target.hostname.endswith('github.com') or target.username or target.password:raise ValueError('unsafe_artifact_redirect')
   with urllib.request.urlopen(urllib.request.Request(signed),timeout=25) as response:
    raw=response.read(35_000_001)
   if len(raw)>35_000_000:raise ValueError("oversized_artifact")
   with zipfile.ZipFile(io.BytesIO(raw)) as archive:
    names=[n for n in archive.namelist() if n.startswith("b95-history/") and n.endswith(".json")]
    if len(names)>1:raise ValueError("unexpected_history_files")
    for name in names:
     if name.count("/")!=1:raise ValueError("unsafe_history_path")
     content=archive.read(name)
     if len(content)>65536:raise ValueError("oversized_history_receipt")
     obj=json.loads(content)
     from v2_b95_b97_history import consolidate
     stamp=obj.get("day","")
     day=date.fromisoformat(stamp)
     if not today-timedelta(days=29)<=day<today:continue
     destination=directory/(str(run_id)+"-"+day.isoformat()+".json")
     destination.write_bytes(content)
     restored+=1
 return {"restored_receipts":restored,"source":"github_actions_successful_runs","release_authorized":False}

if __name__=="__main__":
 from datetime import datetime,timezone
 result=restore(Path("b95-history"),today=datetime.now(timezone.utc).date(),repo=os.environ.get("GITHUB_REPOSITORY",""),token=os.environ.get("GH_READ_TOKEN",""))
 print(json.dumps(result))
