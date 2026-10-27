"""B48 read-only operations readiness: real receipt crash exercise + source alerts.

A successful same-host lab is not a live Discord receipt, operational monitor,
production failover, verified external backup or deployment permission.
"""
from __future__ import annotations
from collections import Counter
from v2_analytics_controls import budget_decision,retention_preview,validate_telemetry
from v2_b39_rollback_rehearsal import exercise_durable_no_send
from v2_b41_production_preflight import inspect_workflows

def evaluate_operations(four:dict,production:dict,durable:dict,*,observed_at:str)->dict:
    if (not isinstance(four,dict) or four.get('schema')!='aggregateit-v2-b47-four-product-held/1'
        or four.get('can_release') is not False or four.get('discord_sent') is not False):
        raise ValueError('untrusted_b47_receipt')
    if not isinstance(production,dict) or production.get('schema')!='aggregateit-v2-b41-readonly-preflight/1':
        raise ValueError('untrusted_production_snapshot')
    if not isinstance(durable,dict) or durable.get('schema')!='aggregateit-v2-b39-no-send-durable-rehearsal/1':
        raise ValueError('untrusted_durable_simulation')
    daily=four.get('daily',{});weekly=four.get('weekly',{})
    if set(daily)!={'english','arabic'} or set(weekly)!={'english','arabic'}:
        raise ValueError('missing_product_cadence')
    if (daily['english'].get('page_count')!=2 or daily['arabic'].get('page_count')!=3
        or daily['english'].get('destination_key')!='discord_webhook'
        or daily['arabic'].get('destination_key')!='discord_webhook_arabic'
        or any(daily[p].get('can_release') is not False for p in daily)):
        raise ValueError('routing_or_product_contract_regression')
    if (durable.get('ambiguous_survived_reopen') is not True
        or durable.get('blind_retry_refused') is not True
        or durable.get('retry_allowed') is not False):
        raise ValueError('unreliable_crash_state')
    alerts=[]
    def add(code, severity,product=None):
        alerts.append({'code':code,'severity':severity,'product':product})
    for product in ('english','arabic'):
        w=weekly[product]
        if (type(w.get('days_with_real_daily_snapshots')) is not int or
            not 0<=w['days_with_real_daily_snapshots']<=7):
            raise ValueError('invalid_weekly_observation_window')
        if w['days_with_real_daily_snapshots']<7:add('weekly_window_not_full', 'warning',product)
        if w.get('pdf_rendered') is not True:add('weekly_pdf_not_generated','warning',product)
        if w.get('complete_seven_day_history') is True and w['days_with_real_daily_snapshots']!=7:
            raise ValueError('forged_full_week_status')
        if daily[product].get('translation_verified') is not False:
            raise ValueError('unverified_translation_promoted')
    if daily['arabic'].get('coverage_gaps'):
        add('arabic_geographic_gaps','warning','arabic')
    for code in production.get('preflight_findings',[]):
        if not isinstance(code,str) or len(code)>180:raise ValueError('invalid_production_incident')
        add(code,'critical' if code.startswith('production_source_floor_') else 'warning')
    add('b45_live_translation_not_authenticated','critical','arabic')
    add('live_discord_receipt_missing','critical')
    add('b49_full_system_shadow_missing','critical')
    unknown=budget_decision(db_size_bytes=None,account_writes_today=None,
                            account_reads_today=None,proposed_writes=2,proposed_reads=2)
    if unknown['permitted'] is not False:raise ValueError('unknown_storage_headroom_allowed')
    telemetry=[validate_telemetry({'idempotency_key':f'b48:{p}:held',
             'kind':'edition','product':p,'status':'withheld','at':observed_at,
             'units':daily[p]['story_count']}) for p in ('english','arabic')]
    retention=retention_preview([],as_of=observed_at)
    if retention['delete_authorized'] is not False:raise ValueError('unapproved_retention_action')
    return {'schema':'aggregateit-v2-b48-operations-readiness/1',
        'status':'HOLD_PRODUCTION_OPERATIONAL_ACCEPTANCE',
        'production_baseline_sha':production['baseline_main_sha'],
        'production_monitoring_configuration_checked':True,
        'production_webhook_and_schedule_execution_verified':False,
        'alert_summary':dict(sorted(Counter(a['severity'] for a in alerts).items())),
        'alerts':alerts,
        'durable_ambiguous_state_persists':True,
        'blind_retry_allowed':False,
        'actual_discord_receipt_verified':False,
        'sqlite_d1_writes':0,'telemetry_records_written_to_db':0,
        'telemetry_events_validated':len(telemetry),
        'optional_telemetry_action':unknown['action'],
        'backup_verified':False,'retention_delete_authorized':False,
        'production_rollback_actuated':False,'cutover_approved':False,
        'model_credits_spent':0,'discord_sent':False,'can_release':False}
