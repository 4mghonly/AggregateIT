"""Read only actual archived V1 GitHub Actions ZIPs using GITHUB_TOKEN actions:read."""
import argparse,json,os
from pathlib import Path
import requests
from v2_b49_archived_edition_gate import inspect_original_zip,assess_original_vs_v2

IDS={'english':12722141477,'arabic':12719355267}
RUNS={'english':40478745761,'arabic':40471115356}
def get_artifact(repo,artifact_id,token):
    if not token:raise ValueError('github_actions_read_token_missing')
    if repo!='4mghonly/AggregateIT':raise ValueError('unapproved_original_repo')
    response=requests.get(f'https://api.github.com/repos/{repo}/actions/artifacts/{artifact_id}/zip',
        headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json'},
        timeout=18,stream=True)
    try:
        if response.status_code!=200:raise ValueError('github_original_artifact_http_'+str(response.status_code))
        payload=bytearray()
        for chunk in response.iter_content(chunk_size=16384):
            payload.extend(chunk)
            if len(payload)>2_500_000:raise ValueError('original_archive_over_cap')
        return bytes(payload)
    finally:response.close()

def execute(token):
    inventory=[]
    for product in ('english','arabic'):
        raw=get_artifact('4mghonly/AggregateIT',IDS[product],token)
        inventory.append(inspect_original_zip(raw,product=product,run_id=RUNS[product]))
    report=assess_original_vs_v2(inventory,v2_observed_at='2026-10-27T09:15:59.555886+00:00')
    return {'schema':'aggregateit-v2-b49-actual-original-archive-inspection/1',
        'originals':inventory,'acceptance':report,
        'github_original_artifact_bytes_uploaded':False,
        'no_prod_changes':True,'no_discord':True,'can_release':False}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',required=True,type=Path)
    opts=p.parse_args()
    try:
        data=execute(os.getenv('GITHUB_TOKEN',''))
    except Exception as exc:
        data={'schema':'aggregateit-v2-b49-actual-original-archive-inspection/1',
              'status':'HOLD_UNABLE_TO_READ_ORIGINALS','failure_class':type(exc).__name__,
              'no_prod_changes':True,'no_discord':True,'can_release':False}
    opts.output.parent.mkdir(parents=True,exist_ok=True)
    opts.output.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps({'status':data.get('acceptance',{}).get('status',data.get('status')),
        'verified_english_artifact':any(x['product']=='english' for x in data.get('originals',[])),
        'verified_arabic_artifact':any(x['product']=='arabic' for x in data.get('originals',[])),
        'can_release':False}))
