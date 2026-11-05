"""B119 independent no-post release-readiness audit. Cannot authorize publication.

Reads only local sanitized CI artifacts and verified paired-run receipts.
Never calls a model, GitHub API, database or delivery endpoint.
"""
from __future__ import annotations
import json
from datetime import date, datetime, timezone, timedelta
from pathlib import Path
from collections import defaultdict

SCHEMAS = {
    "live": "aggregateit-v2-b46-live-chain/1",
    "b115": "aggregateit-v2-b115-seven-day-paired-history/1",
    "shadow": "aggregateit-v2-b49-single-slot-preflight/1",
    "pixel": "aggregateit-v2-b99-pixel-qa/1",
    "history": "aggregateit-v2-b95-b97-history/1",
    "conflicts": "aggregateit-v2-b112-history-conflicts/1",
}

def _load(path):
    try:
        raw=Path(path).read_bytes()
        if len(raw)>500000: return {}
        value=json.loads(raw)
        return value if isinstance(value,dict) else {}
    except (OSError,ValueError,TypeError):
        return {}

def stable_candidate_sha(directory, window, *,today):
    """Require a genuine bilingual-positive GitHub-run-backed receipt on each date."""
    from v2_b115_pair_history import NAME, verify_pair
    if not isinstance(window,list) or len(window)!=7 or len(set(window))!=7:
        return None
    by_date=defaultdict(set)
    root=Path(directory)
    for file in (sorted(root.glob('*.json')) if root.is_dir() else []):
        match=NAME.fullmatch(file.name)
        if not match or file.is_symlink() or file.stat().st_size>65536:
            return None
        try:
            receipt=verify_pair(json.loads(file.read_bytes()),run_id=match['run'],
                                expected_day=match['day'],today=today)
        except (ValueError,KeyError,TypeError,UnicodeDecodeError):
            return None
        if receipt['utc_date'] not in window:
            continue
        if all(receipt['products'][p]['operational_v2_selected']>0 for p in ('english','arabic')):
            by_date[receipt['utc_date']].add(receipt['head_sha'])
    if any(not by_date[day] for day in window):
        return None
    candidates=set.intersection(*(by_date[day] for day in window))
    return sorted(candidates)[0] if candidates else None

def assess(live, b115, shadow, pixel, history, conflicts, *,candidate_sha=None):
    verified={name:isinstance(value,dict) and value.get('schema')==SCHEMAS[name]
              and value.get('can_release') is False for name,value
              in (('live',live),('b115',b115),('shadow',shadow),
                  ('pixel',pixel),('history',history),('conflicts',conflicts))}
    dates=b115.get('window',[]) if verified['b115'] else []
    consecutive=False
    if isinstance(dates,list) and len(dates)==7 and len(set(dates))==7:
        try:
            days=[date.fromisoformat(day) for day in dates]
            consecutive=all(days[i+1]-days[i]==timedelta(days=1) for i in range(6))
        except (ValueError,TypeError):
            consecutive=False
    bilingual=bool(consecutive and verified['b115']
        and b115.get('seven_positive_bilingual_days') is True
        and b115.get('seven_distinct_paired_capture_dates') is True
        and all(isinstance(b115.get('daily',{}).get(day),dict)
                and b115['daily'][day].get('capture_runs',0)>0
                and b115['daily'][day].get('english_positive') is True
                and b115['daily'][day].get('arabic_positive') is True
                for day in dates))
    four=live.get('four_products',{}) if verified['live'] else {}
    native=live.get('native',{}) if verified['live'] else {}
    dims={
        'b115_seven_genuine_bilingual_dates':bilingual,
        'stable_candidate_seven_genuine_dates':bool(bilingual and candidate_sha),
        'v2_four_held_products':four.get('schema')=='aggregateit-v2-b47-four-product-held/1',
        'v2_five_native_pages':native.get('status')=='HELD_VALID_NATIVE_PAGES'
            and len(native.get('native_pages',[]))==5,
        'v2_objective_pixel_checks':verified['pixel'] and pixel.get('all_objective_checks_pass') is True,
        'b95_conflict_free_in_current_sample':verified['conflicts'] and conflicts.get('conflicting_days')==0,
        'b95_authentic_seven_day_history':verified['history'] and history.get('seven_day_evidence_met') is True,
        'v2_weekly_both_languages_seven_real_days':four.get('real_7_day_reporting_verified') is True,
        'v1_full_editorial_and_model_parity':False,
        'v1_v2_arabic_translation_fallback_parity':False,
        'v1_v2_same_slot_visual_equivalence':False,
        'v1_v2_authenticated_delivery_and_rollback_parity':False,
        'editorial_disagreements_independently_adjudicated':False,
        'publisher_republication_rights_and_factuality':False,
    }
    return {
        'schema':'aggregateit-v2-b119-independent-release-audit/1',
        'release_status':'HOLD',
        'fixed_candidate_sha_with_seven_dates':candidate_sha if dims['stable_candidate_seven_genuine_dates'] else None,
        'input_schema_verified':verified,
        'gates':dims,
        'passed_gates':[key for key,value in dims.items() if value],
        'outstanding_gates':[key for key,value in dims.items() if not value],
        'parser_parity_is_not_full_model_visual_delivery_parity':True,
        'manual_owner_review_required':True,
        'no_live_model_calls':True,
        'no_discord_posts':True,
        'can_release':False,
    }

def main():
    live=_load('b80_b81_live_editorial.json')
    b115=_load('b115_seven_day_history.json')
    shadow=_load('b83_same_slot_shadow.json')
    pixel=_load('b99_pixel_qa.json')
    history=_load('b95_b97_history.json')
    conflicts=_load('b112_history_conflicts.json')
    today=datetime.now(timezone.utc).date()
    sha=stable_candidate_sha('b115-history',b115.get('window',[]),today=today)
    result=assess(live,b115,shadow,pixel,history,conflicts,candidate_sha=sha)
    Path('b119_release_readiness.json').write_text(
        json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf8')
    print(json.dumps({'release_status':result['release_status'],
          'passed_gates':result['passed_gates'],
          'outstanding_gates':result['outstanding_gates'],
          'can_release':False},sort_keys=True))

if __name__=='__main__':
    main()
