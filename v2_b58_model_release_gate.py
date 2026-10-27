"""B58 model selection only: strict non-production release blockers."""
import json
from pathlib import Path
def assess_selection(config:dict, *, recorded_full_v1_v2_match:bool=False)->dict:
    if config.get('schema')!='aggregateit-v2-b58-model-selection/1':
        raise ValueError('untrusted_selection')
    if config.get('api_base')!='https://openrouter.ai/api/v1' or config.get('key_secret_name')!='LLM_API_KEY':
        raise ValueError('unsafe_key_or_model_route')
    a,b=config['primary'],config['fallback']
    if (a['model']!='google/gemini-3.1-flash-lite' or
        b['model']!='openai/gpt-oss-120b' or a['family']==b['family']):
        raise ValueError('unverified_model_family')
    bud=config['budget'];activation=config['activation']
    if (type(bud['approved_usd']) not in (float,int) or
        bud['approved_usd']!=.50 or
        bud['spent_reported_b55_b56_b57_usd']>bud['approved_usd'] or
        bud['conservative_reserved_b55_b56_b57_usd']>bud['approved_usd']):
        raise ValueError('budget_acceptance_violation')
    if activation['enabled'] is not False or activation['production_model_changes_authorized'] is not False:
        raise ValueError('unauthorized_activation')
    open_items=[]
    if not activation['full_real_news_source_translation_accepted']:open_items.append('b45_actual_publisher_translation_not_verified')
    if not activation['live_primary_outage_proven']:open_items.append('live_primary_outage_not_observed')
    if not activation['translated_publisher_rights_verified']:open_items.append('source_content_rights_not_verified')
    if not recorded_full_v1_v2_match or not activation['full_original_v1_v2_same_slot_proven']:
        open_items.append('v1_v2_same_slot_full_edition_quality_not_verified')
    if not activation['discord_client_receipts_verified']:open_items.append('independent_discord_client_receipts_missing')
    open_items.extend(['original_english_title_lead_mismatch_qa',
        'original_english_chart_label_clipping_qa',
        'original_arabic_uae_priority_coverage_gap',
        'original_arabic_content_density_qa',
        'production_source_audit_dependency_failure',
        'seven_genuine_weekly_days_not_recorded'])
    return {'schema':'aggregateit-v2-b58-release-gate/1',
            'model_primary_staged':a['model'],'model_fallback_staged':b['model'],
            'same_openrouter_secret_reused':True,'model_configuration_enabled':False,
            'budget_remaining_at_reported_rates':round(.5-bud['spent_reported_b55_b56_b57_usd'],7),
            'unresolved':open_items,'release_status':'HOLD',
            'production_main_modified':False,'discord_sent':False,'can_release':False}
def main():
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--output',required=True,type=Path)
    a=p.parse_args()
    source=json.loads(Path('config/v2/b58_staged_paid_models.json').read_text())
    result=assess_selection(source)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'release_status':result['release_status'],
       'outstanding':len(result['unresolved']),'can_release':False}))
if __name__=='__main__':main()
