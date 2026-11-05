"""B121 B95 history preservation: quarantine contradictory digests, never backfill.

This inspects supplied original receipts; it does not select the most
favourable same-day version, delete conflicting records or reissue receipts.
"""
from __future__ import annotations
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path
import json,re

NAME=re.compile(r'(?:(?P<run>[1-9][0-9]{0,17})-)?(?P<day>[0-9]{4}-[0-9]{2}-[0-9]{2})\.json\Z')
SHA=re.compile(r'[0-9a-f]{64}\Z')
SCHEMA='aggregateit-v2-b121-b95-quarantine/1'

def inspect_b95_provenance(directory,*,today):
    if type(today) is not date:raise ValueError('invalid_target_date')
    root=Path(directory)
    files=sorted(root.glob('*.json')) if root.is_dir() else []
    if len(files)>60:raise ValueError('unbounded_history_audit')
    by_day=defaultdict(list)
    unattributed=[]
    for file in files:
        match=NAME.fullmatch(file.name)
        if not match or file.is_symlink() or file.stat().st_size>65536:
            raise ValueError('untrusted_history_file')
        row=json.loads(file.read_bytes())
        stamp=date.fromisoformat(row.get('day',''))
        if stamp.isoformat()!=match['day'] or stamp>today or stamp<today-timedelta(days=30):
            raise ValueError('history_filename_date_mismatch')
        counts=row.get('stories')
        if (row.get('schema')!='aggregateit-v2-b95-daily-history/1'
            or row.get('can_release') is not False
            or not isinstance(counts,dict) or set(counts)!={'english','arabic'}
            or any(type(v) is not int or not 0<=v<=30 for v in counts.values())
            or not isinstance(row.get('evidence_sha256'),str)
            or not SHA.fullmatch(row['evidence_sha256'])):
            raise ValueError('invalid_history_receipt')
        if match['run'] is None:
            unattributed.append(file.name)
        by_day[match['day']].append({'filename':file.name,'run_id':match['run'],
            'stories':counts,'digest':row['evidence_sha256']})
    days={};quarantined=[]
    for day,entries in sorted(by_day.items()):
        variants={(r['stories']['english'],r['stories']['arabic'],r['digest']) for r in entries}
        conflict=len(variants)>1
        if conflict:quarantined.append(day)
        days[day]={'receipt_files':len(entries),'variants':len(variants),
            'quarantined':conflict,
            'variant_evidence_sha256':sorted({v[2] for v in variants}),
            'github_run_id_hints':sorted({r['run_id'] for r in entries if r['run_id']})}
    consistent=sum(not x['quarantined'] for x in days.values())
    seven_dates=[(today-timedelta(days=i)).isoformat() for i in range(6,-1,-1)]
    seven=all(day in days and not days[day]['quarantined'] for day in seven_dates)
    # Digest and run-ID strings alone do not authenticate GitHub jobs.
    return {'schema':SCHEMA,'receipt_files':len(files),'days':days,
            'distinct_consistent_days':consistent,'quarantined_days':quarantined,
            'unattributed_files':sorted(unattributed),
            'seven_day_release_evidence_met':False,
            'seven_day_consistent_receipt_days':seven,
            'source_github_run_provenance_verified':False,
            'history_accepted':False,  # no authenticated GitHub run lineage in local receipts
            'release_status':'HOLD', 'backfill_performed':False,
            'receipts_modified_or_deleted':False,'can_release':False}

if __name__=='__main__':
    import argparse
    from datetime import datetime,timezone
    p=argparse.ArgumentParser();p.add_argument('--directory',default='b95-history')
    p.add_argument('--output',default='b121_b95_quarantine.json')
    args=p.parse_args()
    report=inspect_b95_provenance(args.directory,today=datetime.now(timezone.utc).date())
    Path(args.output).write_text(json.dumps(report,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'b95_quarantined_days':report['quarantined_days'],
                      'consistent_days':report['distinct_consistent_days'],
                      'source_run_authenticated':False,'release_status':'HOLD'}))
