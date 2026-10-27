"""B40 offline stage audit. Parser parity and synthetic images are NOT full parity."""
from __future__ import annotations

PRODUCTS = {'english': (2,'discord_webhook'), 'arabic': (3,'discord_webhook_arabic')}

def assess_full_shadow(capture: dict, native: dict, packets: dict) -> dict:
    if not isinstance(capture,dict) or capture.get('schema')!='aggregateit-v2-b38-live-parser-pair/1':
        raise ValueError('untrusted_capture_comparison')
    if not isinstance(native,dict) or native.get('schema')!='aggregateit-v2-native-no-post-pages/1':
        raise ValueError('untrusted_native_preview')
    if (native.get('delivery_authorized') is not False or native.get('discord_sent') is not False
            or native.get('llm_called') is not False or native.get('source_facts_verified') is not False):
        raise ValueError('unsafe_native_preview_claim')
    if not isinstance(packets,dict) or set(packets)!=set(PRODUCTS):
        raise ValueError('missing_bilingual_packets')
    pages=native.get('pages')
    if not isinstance(pages,list) or len(pages)!=5:
        raise ValueError('wrong_page_count')
    for product,(count,destination) in PRODUCTS.items():
        packet=packets[product]
        if (not isinstance(packet,dict) or packet.get('schema')!='aggregateit-v2-discord-preview/1'
                or packet.get('product')!=product or packet.get('destination_key')!=destination
                or packet.get('message_count')!=1 or packet.get('can_send') is not False
                or packet.get('synthetic') is not True or packet.get('webhook_url') is not None):
            raise ValueError('unsafe_or_wrong_destination_packet')
        attachments=packet.get('attachments')
        product_pages=[p for p in pages if isinstance(p,dict) and p.get('product')==product]
        if len(product_pages)!=count or not isinstance(attachments,list) or len(attachments)!=count:
            raise ValueError('page_packet_count_disagree')
        for n,(page,attachment) in enumerate(zip(product_pages,attachments),1):
            if (page.get('page')!=n or not isinstance(page.get('sha256'),str)
                    or len(page['sha256'])!=64 or attachment.get('sha256')!=page['sha256']
                    or type(attachment.get('size_bytes')) is not int or attachment['size_bytes']<8):
                raise ValueError('page_packet_integrity_mismatch')
    captures=capture.get('results')
    if not isinstance(captures,list):
        raise ValueError('invalid_capture_rows')
    observed={r.get('product') for r in captures if isinstance(r,dict) and r.get('status')=='COMPARED'}
    if capture.get('status')=='COMPARED' and observed!=set(PRODUCTS):
        raise ValueError('contradictory_capture_status')
    parser_success=capture.get('status')=='COMPARED' and capture.get('parity_all') is True
    return {'schema':'aggregateit-v2-b40-stage-audit/1',
            'status':'HOLD_FULL_SYSTEM_COMPARISON',
            'stage_evidence':{
                'live_exact_input_v1_v2_parsers':parser_success,
                'synthetic_native_2_english_3_arabic_pngs':True,
                'synthetic_discord_packet_integrity':True,
                'real_article_body_evidence_both':False,
                'same_input_v1_v2_editorial':False,
                'same_input_model_and_translation':False,
                'same_input_full_native_pngs':False,
                'real_discord_client_delivery':False},
            'independent_products':sorted(PRODUCTS),
            'native_preview_page_count':len(pages),
            'no_post_packet_message_count':2,
            'unmet':['same_input_article_body_and_source_evidence',
                     'v1_v2_editorial_selection_and_attribution',
                     'matching_model_translation_policy_or_declared_abstention',
                     'matching_genuine_news_native_rendering',
                     'authenticated_external_delivery_and_device_qa'],
            'source_input_only_matched_at_parser':parser_success,
            'full_system_metric_deltas_allowed':False,
            'synthetic_render_is_not_live_news':True,
            'can_release':False,'discord_sent':False,'main_modified':False}
