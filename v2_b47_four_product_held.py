"""B47: four held products from ONE B46 source-backed bilingual editorial snapshot.

Daily: 2 English + 3 Arabic 4K PNGs and non-sendable Discord packets.
Weekly: English + Arabic source-bound HTML previews for the available window.
A single day of genuine evidence is not silently promoted to 7-day coverage.
Publisher/article originals and rendered bytes never enter returned metrics.
"""
from __future__ import annotations
from datetime import datetime
from hashlib import sha256
from pathlib import Path
from v2_b46_native_held import render_genuine_held
from v2_discord_edition import prepare_discord_edition
from v2_weekly_rollup import rollup_week
from v2_weekly_layout import render_weekly_html, AR_REGIONS

def compose_held_products(editorial:dict, *, output_dir:Path, as_of:str)->dict:
    if (not isinstance(editorial,dict)
        or editorial.get('schema')!='aggregateit-v2-b46-article-editorial/1'
        or editorial.get('can_send') is not False
        or editorial.get('live_model_translation_verified') is not False):
        raise ValueError('untrusted_bilingual_editorial')
    products=editorial.get('products')
    if not isinstance(products,dict) or set(products)!= {'english','arabic'}:
        raise ValueError('two_distinct_products_required')
    if any(products[p].get('story_count',0)<1 for p in ('english','arabic')):
        raise ValueError('cannot_substitute_synthetic_missing_product')
    try:
        t=datetime.fromisoformat(as_of.replace('Z','+00:00'))
        if t.utcoffset() is None:raise ValueError('time')
    except (TypeError,AttributeError,ValueError):
        raise ValueError('invalid_product_window') from None
    daily_native=render_genuine_held(editorial,output_dir=Path(output_dir))
    if daily_native['status']!='HELD_VALID_NATIVE_PAGES':
        raise ValueError('invalid_native_receipts')
    daily={};weekly={}
    for product in ('english','arabic'):
        plan=products[product].get('editorial_plan')
        if plan is None or plan.get('delivery_authorized') is not False:
            raise ValueError('untrusted_editorial_plan')
        image_pages=[]
        for record in daily_native['native_pages']:
            if record['product']!=product:continue
            path=Path(output_dir)/f'{product}-no-post-{record["page"]}.png'
            blob=path.read_bytes()
            if sha256(blob).hexdigest()!=record['sha256']:
                raise ValueError('disk_png_hash_mismatch')
            image_pages.append({'filename':path.name,'content':blob,'sha256':record['sha256']})
        topics=['geopolitics','markets'] if product=='english' else ['geopolitics','security']
        represented=products[product]['represented_regions']
        gaps=sorted(set(AR_REGIONS)-set(represented)) if product=='arabic' else []
        packet=prepare_discord_edition(product=product,cadence='daily',
            slot_id=plan['slot_id'],pages=image_pages,
            headline=('Genuine excerpt laboratory | no release' if product=='english'
                      else 'تجربة اقتباسات موثقة المصدر — غير مخصصة للنشر'),
            summary=[],included_topics=topics,regions=represented,
            coverage_gaps=gaps,critical_review='insufficient_evidence',
            synthetic=True)
        if packet['message_count']!=1 or packet['can_send'] is not False:
            raise ValueError('sendable_daily_packet_forbidden')
        daily[product]={'schema':packet['schema'],'page_count':len(image_pages),
            'native_page_sha256':[p['sha256'] for p in image_pages],
            'destination_key':packet['destination_key'],
            'one_held_message':packet['message_count']==1,
            'story_count':products[product]['story_count'],
            'regions_covered':represented,'coverage_gaps':gaps,
            'real_source_backed':True,'market_values_verified':False,
            'translation_verified':False,'discord_sent':False,'can_release':False}
        report=rollup_week([plan],product=product,as_of=as_of,market_snapshots=[])
        html=render_weekly_html(report)
        if not (f'lang="{"en" if product=="english" else "ar"}"' in html
               and f'dir="{"ltr" if product=="english" else "rtl"}"' in html):
            raise ValueError('wrong_weekly_page_language')
        weekly[product]={'schema':report['schema'],
            'source_bound_event_count':report['unique_events'],
            'days_with_real_daily_snapshots':report['days_with_snapshots'],
            'required_full_week_days':7,
            'complete_seven_day_history':report['days_with_snapshots']==7,
            'html_sha256':sha256(html.encode('utf8')).hexdigest(),
            'html_bytes':len(html.encode('utf8')),
            'html_accessible_in_memory_only':True,
            'pdf_rendered':False,'discord_packet_prepared':False,
            'market_values_verified':False,'naysayer_status':report['naysayer_status'],
            'can_release':False}
    return {'schema':'aggregateit-v2-b47-four-product-held/1','daily':daily,'weekly':weekly,
        'formats_tested':['english_daily_2png','arabic_daily_3png',
                          'english_weekly_html','arabic_weekly_html'],
        'real_7_day_reporting_verified':all(r['complete_seven_day_history'] for r in weekly.values()),
        'weekly_pdf_produced':False,'weekly_discord_send_ready':False,
        'independent_story_factuality_verified':False,
        'live_translation_performed':False,
        'publisher_republication_rights_verified':False,
        'discord_sent':False,'can_release':False}
