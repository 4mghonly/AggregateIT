"""B40 live parser receipts plus independent synthetic native/page/packet rehearsal.

Tracks intentionally are NOT joined into a genuine full-system replay.
Only aggregate metrics and hashes leave this runner. No posting or models.
"""
from __future__ import annotations
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
import json
from PIL import Image
from v2_arabic_application_rehearsal import arabic_synthetic_fixture
from v2_b38_live_pair import run_live_pairs
from v2_b40_stage_acceptance import assess_full_shadow
from v2_discord_edition import prepare_discord_edition
from v2_native_evidence_render import render_held_editions
from v2_offline_rehearsal import run_offline_rehearsal

def run_b40() -> dict:
    capture=run_live_pairs()
    registry=json.loads((Path(__file__).parent/'config/v2/source_registry.json').read_text(encoding='utf8'))
    fixture=arabic_synthetic_fixture()
    rehearsal=run_offline_rehearsal(fixture,registry)
    plans={p:rehearsal['products'][p]['plan'] for p in ('english','arabic')}
    packets={}
    with TemporaryDirectory(prefix='aggregateit-b40-held-') as temp:
        directory=Path(temp)/'native'
        native=render_held_editions(plans['english'],plans['arabic'],slot_id=fixture['slot_id'],output_dir=directory)
        for product,count,topics in (('english',2,['geopolitics','markets']),
                                     ('arabic',3,['geopolitics','security'])):
            page_rows=[]
            for page in native['pages']:
                if page['product']!=product:continue
                data=(directory/page['path']).read_bytes()
                if sha256(data).hexdigest()!=page['sha256']:
                    raise ValueError('native_page_checksum_mismatch')
                with Image.open(directory/page['path']) as image:
                    if image.size!=(3840,2160) or image.format!='PNG':
                        raise ValueError('invalid_native_png')
                    image.verify()
                page_rows.append({'filename':page['path'],'content':data,'sha256':page['sha256']})
            if len(page_rows)!=count:raise ValueError('native_page_count_mismatch')
            packets[product]=prepare_discord_edition(
                product=product,cadence='daily',slot_id=fixture['slot_id'],
                pages=page_rows,
                headline=('Synthetic evidence Gazette' if product=='english' else 'اختبار اصطناعي لموجز المصادر'),
                summary=(['Synthetic evidence only. No live news or model analysis.'] if product=='english'
                         else ['مواد تجريبية فقط دون تحليل لأخبار حقيقية']),
                included_topics=topics,regions=list(plans[product]['represented_regions']),
                coverage_gaps=[],critical_review='insufficient_evidence',synthetic=True)
        audit=assess_full_shadow(capture,native,packets)
        if audit['can_release'] is not False:raise ValueError('unexpected_acceptance_promotion')
        return {'schema':'aggregateit-v2-b40-execution/1','assessment':audit,
                'authentic_parser_capture':capture,
                'synthetic_native_png_receipts':[{'product':p['product'],'page':p['page'],
                                               'sha256':p['sha256']} for p in native['pages']],
                'synthetic_packet_summary':{p:{'destination_key':packets[p]['destination_key'],
                                             'message_count':packets[p]['message_count'],
                                             'attachment_count':len(packets[p]['attachments']),
                                             'can_send':packets[p]['can_send']} for p in packets},
                'real_article_to_newsletter_replay':False,
                'live_llm_or_translation_executed':False,
                'raw_publisher_bytes_retained':False,
                'discord_sent':False,'main_modified':False}

def main():
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('--output',required=True)
    args=ap.parse_args()
    result=run_b40()
    dest=Path(args.output);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
    print(json.dumps({'status':result['assessment']['status'],
                      'parser_parity':result['assessment']['stage_evidence']['live_exact_input_v1_v2_parsers'],
                      'native_pages':len(result['synthetic_native_png_receipts']),
                      'can_release':result['assessment']['can_release']}))
    return 0

if __name__=='__main__':raise SystemExit(main())
