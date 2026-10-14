"""Skip duplicate scheduled slots after an independent scheduler dispatch."""
import json,os,time,urllib.request
from datetime import datetime,timezone

SCHEDULES={'engine.yml':(3600,7*60),'arabic-scheduler.yml':(21600,2*3600),'slide.yml':(86400,11*3600+30*60)}

def slot_start(workflow,now=None):
    period,offset=SCHEDULES[workflow];now=time.time() if now is None else now
    return int((now-offset)//period*period+offset)

def duplicate(runs,workflow,now=None,current_id=None):
    slot=slot_start(workflow,now)
    for run in runs:
        if str(run.get('id'))==str(current_id):continue
        if run.get('status')!='completed' or run.get('conclusion')!='success':continue
        ts=datetime.fromisoformat(run['created_at'].replace('Z','+00:00')).timestamp()
        if ts>=slot:return True
    return False

def main():
    workflow=os.environ['CADENCE_WORKFLOW'];repo=os.getenv('GITHUB_REPOSITORY','4mghonly/AggregateIT')
    scheduled=os.getenv('GITHUB_EVENT_NAME')=='schedule' or bool(os.getenv('SCHEDULER_SLOT'))
    proceed=True
    if scheduled:
        req=urllib.request.Request(f'https://api.github.com/repos/{repo}/actions/workflows/{workflow}/runs?branch=main&per_page=20',headers={'Authorization':'Bearer '+os.environ['GITHUB_TOKEN'],'Accept':'application/vnd.github+json','User-Agent':'AggregateIT-cadence'})
        with urllib.request.urlopen(req,timeout=20) as r:runs=json.load(r)['workflow_runs']
        proceed=not duplicate(runs,workflow,current_id=os.getenv('GITHUB_RUN_ID'))
    with open(os.environ['GITHUB_OUTPUT'],'a') as out:out.write('proceed='+str(proceed).lower()+'\n')
    print('Scheduled slot '+('eligible' if proceed else 'already completed; skipping duplicate'))

if __name__=='__main__':main()
