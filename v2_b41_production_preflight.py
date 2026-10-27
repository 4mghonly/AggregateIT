"""B41 production baseline and rollback *preflight* (read-only, never deploy).

Uses separately checked-out GitHub production main files. YAML config presence
is not runtime health; this module makes no claim of secrets or Discord checks.
"""
from __future__ import annotations
from hashlib import sha256
from pathlib import Path
import re
import subprocess
import yaml

FILES=('.github/workflows/engine.yml','.github/workflows/slide.yml',
       '.github/workflows/arabic-scheduler.yml',
       '.github/workflows/arabic-source-audit.yml',
       '.github/workflows/operations-watchdog.yml')
V1_PARSERS=('main.py','arabic_newsletter/collect.py')
EXPECTED_CRONS={
    'arabic-scheduler.yml':{'0 2 * * *','0 8 * * *','0 14 * * *','0 20 * * *'},
    'slide.yml':{'30 11 * * *'},
    'engine.yml':{'7 * * * *'},
}
EXPECTED_NAMES={
    'arabic-scheduler.yml':'Arabic Briefing V2 Production',
    'slide.yml':'Intelligence Slide Deck',
    'engine.yml':'News Intelligence Engine',
}

def _revision(root):
    value=subprocess.run(['git','-C',str(root),'rev-parse','HEAD'],capture_output=True,
                          text=True,check=True,timeout=5).stdout.strip()
    if not re.fullmatch('[0-9a-f]{40}',value):raise ValueError('untrusted_git_revision')
    return value

def inspect_workflows(*, baseline_root:Path, candidate_root:Path, main_sha:str|None=None):
    baseline_root=Path(baseline_root);candidate_root=Path(candidate_root)
    if not baseline_root.is_dir() or not candidate_root.is_dir():
        raise ValueError('missing_checkout_directory')
    actual_sha=_revision(baseline_root)
    if main_sha is not None and actual_sha!=main_sha:
        raise ValueError('baseline_revision_mismatch')
    candidate_sha=_revision(candidate_root)
    if candidate_sha==actual_sha:raise ValueError('same_baseline_and_candidate')
    rows=[];failures=[]
    for rel in FILES:
        a=baseline_root/rel;b=candidate_root/rel
        if not a.is_file() or not b.is_file():raise ValueError('missing_production_workflow')
        raw=a.read_bytes()
        parsed=yaml.load(raw,Loader=yaml.BaseLoader)
        if not isinstance(parsed,dict) or not isinstance(parsed.get('jobs'),dict):
            raise ValueError('invalid_production_workflow')
        events=parsed.get('on')
        if not isinstance(events,dict):raise ValueError('missing_production_triggers')
        schedule=events.get('schedule') or []
        crons={row['cron'] for row in schedule if isinstance(row,dict) and 'cron' in row}
        label=Path(rel).name
        diff=raw!=b.read_bytes()
        row={'workflow':label,'production_sha256':sha256(raw).hexdigest(),
             'branch_workflow_same_as_main':not diff,
             'has_schedule':bool(schedule),'cron_entries':len(crons),
             'has_dispatch':'workflow_dispatch' in events,
             'has_jobs':bool(parsed.get('jobs'))}
        if label in EXPECTED_CRONS:
            row['expected_cron_matches']=crons==EXPECTED_CRONS[label]
            row['expected_name_matches']=parsed.get('name')==EXPECTED_NAMES[label]
            if not row['expected_cron_matches']:failures.append('schedule_mismatch_'+label)
            if not row['expected_name_matches']:failures.append('unexpected_job_name_'+label)
        if diff:failures.append('candidate_production_workflow_drift_'+label)
        rows.append(row)
    legacy={}
    for rel in V1_PARSERS:
        src=(baseline_root/rel).read_bytes();dst=(candidate_root/rel).read_bytes()
        legacy[rel]={'main_blob_sha256':sha256(src).hexdigest(),'unchanged_in_candidate':src==dst}
        if src!=dst:failures.append('legacy_parser_changed_'+rel.replace('/','_'))
    audit=(baseline_root/FILES[3]).read_text(encoding='utf8')
    audit_writes_main=('git push origin HEAD:main' in audit)
    if audit_writes_main:
        failures.append('production_audit_can_advance_main_during_canary')
    return {'schema':'aggregateit-v2-b41-readonly-preflight/1',
            'baseline_main_sha':actual_sha,'candidate_v2_sha':candidate_sha,
            'workflow_snapshots':rows,'legacy_parsers':legacy,
            'main_auto_write_workflow_present':audit_writes_main,
            'preflight_findings':sorted(set(failures)),
            'status':'HOLD_PRODUCTION_CANARY',
            'authenticated_external_delivery':False,'live_discord_client_verified':False,
            'model_fallback_verified':False,'rollback_actuated':False,
            'production_route_changed':False,'can_release':False,'discord_sent':False}
