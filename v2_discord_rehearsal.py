"""B5/B6 NO-POST bridge: real V2 synthetic renderer -> safe Discord manifest.

Imports existing offline renderer bridges, never live collection or sending.
"""
from __future__ import annotations
from v2_discord_edition import prepare_discord_edition

def rehearse_discord_bundle(*, product: str, registry: dict) -> dict:
    if product == 'english':
        from v2_english_application_rehearsal import synthetic_fixture, rehearse_english
        fixture=synthetic_fixture()
        result=rehearse_english(fixture,registry)
    elif product == 'arabic':
        from v2_arabic_application_rehearsal import arabic_synthetic_fixture, rehearse_arabic
        fixture=arabic_synthetic_fixture()
        result=rehearse_arabic(fixture,registry)
    else:
        raise ValueError('unsupported_discord_rehearsal_product')
    if result.get('discord_sent') is not False or result.get('synthetic') is not True:
        raise ValueError('unsafe_upstream_rehearsal_result')
    pages=[{'filename':f'aggregateit-{product}-daily-{p["page_number"]}.png',
            'content':p['png'],'sha256':p['sha256']} for p in result['pages']]
    regions=sorted({x['region'] for x in fixture['documents']})
    manifest=prepare_discord_edition(
        product=product,cadence='daily',slot_id=fixture['slot_id'],pages=pages,
        headline=('Evidence-gated synthetic Gazette' if product=='english'
                  else 'نشرة تجريبية موثقة المصدر'),
        summary=(['No real financial data supplied; this is an editorial proof only.']
                 if product=='english' else ['المحتوى اختباري ولا يتضمن أخباراً حقيقية.']),
        included_topics=(['geopolitics','markets'] if product=='english'
                         else ['geopolitics','security']),
        regions=regions,coverage_gaps=[],
        critical_review='insufficient_evidence',synthetic=True)
    return {'schema':'aggregateit-v2-discord-rehearsal/1','product':product,
            'manifest':manifest,'rendered_page_count':len(result['pages']),
            'source_ids':result['source_ids'],'evidence_receipt':result['evidence_receipt'],
            'discord_sent':False,'live_model_called':False,
            'source_quality':'synthetic_unverified',
            'market_data':result.get('market_data','not_applicable')}
