"""Offline packaging gate for one Discord message per AggregateIT edition.

No network sender, no webhook URL, no production side effects.
"""
from __future__ import annotations
from datetime import datetime
from hashlib import sha256
import re

EN_TOPICS = frozenset({'geopolitics','markets','finance','macro','energy','security','trade','policy'})
AR_TOPICS = frozenset({'geopolitics','military','diplomacy','security','political_stability','humanitarian_conflict','strategic_infrastructure','sanctions'})
DESTINATIONS = {'english':'discord_webhook','arabic':'discord_webhook_arabic'}
CRITICAL = frozenset({'supported_challenge','assessment_survives','insufficient_evidence','withheld'})
PNG_MAGIC = b'\x89PNG\r\n\x1a\n'
MAX_FILE_SIZE = 8 * 1024 * 1024  # Conservative internal upload budget, not provider's advertised cap.

def _single_line(value: str, cap: int) -> str:
    if not isinstance(value,str):
        raise ValueError('invalid_message_text')
    value=re.sub(r'\s+',' ',value).strip()
    return value.replace('@','＠').replace('<','‹').replace('>','›')[:cap]

def _validate_slot(slot_id: str) -> str:
    try: dt=datetime.fromisoformat(slot_id)
    except (TypeError,ValueError) as exc: raise ValueError('invalid_slot_id') from exc
    if dt.tzinfo is None or dt.utcoffset() is None: raise ValueError('slot_timezone_required')
    return dt.isoformat()

def prepare_discord_edition(*, product: str, cadence: str, slot_id: str,
                            pages: list[dict], headline: str, summary: list[str],
                            included_topics: list[str], regions: list[str],
                            coverage_gaps: list[str] | None = None,
                            critical_review: str = 'insufficient_evidence',
                            synthetic: bool = True) -> dict:
    if synthetic is not True: raise ValueError('non_synthetic_discord_packaging_not_authorized')
    if product not in DESTINATIONS or cadence not in {'daily','weekly'}: raise ValueError('unknown_product_or_cadence')
    slot=_validate_slot(slot_id)
    if not isinstance(included_topics,list) or not included_topics or any(not isinstance(x,str) for x in included_topics):
        raise ValueError('invalid_topics')
    topics=set(included_topics)
    if product=='arabic' and not topics <= AR_TOPICS: raise ValueError('arabic_financial_topic_forbidden')
    if product=='english' and cadence=='daily' and ('geopolitics' not in topics or not topics.intersection({'markets','finance','macro'})):
        raise ValueError('english_daily_requires_geo_and_markets')
    if product=='english' and not topics <= EN_TOPICS: raise ValueError('invalid_english_topic')
    if critical_review not in CRITICAL: raise ValueError('invalid_critical_review_status')
    if not isinstance(summary,list) or len(summary)>6 or any(not isinstance(x,str) for x in summary):
        raise ValueError('invalid_summary')
    if not isinstance(regions,list) or len(regions)>25 or any(not isinstance(x,str) for x in regions):
        raise ValueError('invalid_region_list')
    if coverage_gaps is None: coverage_gaps=[]
    if not isinstance(coverage_gaps,list) or len(coverage_gaps)>25 or any(not isinstance(x,str) for x in coverage_gaps):
        raise ValueError('invalid_coverage_gaps')
    if not isinstance(pages,list) or not 1<=len(pages)<=10: raise ValueError('invalid_discord_attachment_count')
    if cadence=='daily' and len(pages)!=(2 if product=='english' else 3):
        raise ValueError('unexpected_daily_page_count')
    attachments=[];fmt=None;names=set()
    for index,page in enumerate(pages,1):
        if not isinstance(page,dict) or set(page)!={'filename','content','sha256'}:
            raise ValueError('invalid_attachment_fields')
        name=page['filename'];raw=page['content'];digest=page['sha256']
        if not isinstance(name,str) or not re.fullmatch(r'[a-zA-Z0-9_.-]{1,80}\.(png|pdf)',name):
            raise ValueError('invalid_attachment_name')
        if name in names: raise ValueError('duplicate_attachment_name')
        names.add(name)
        ext=name.rsplit('.',1)[-1]
        if fmt is not None and fmt!=ext: raise ValueError('mixed_attachment_formats')
        fmt=ext
        if not isinstance(raw,bytes) or not raw or len(raw)>MAX_FILE_SIZE: raise ValueError('invalid_attachment_size')
        if (ext=='png' and not raw.startswith(PNG_MAGIC)) or (ext=='pdf' and not raw.startswith(b'%PDF-')):
            raise ValueError('file_signature_mismatch')
        actual=sha256(raw).hexdigest()
        if actual!=digest: raise ValueError('attachment_checksum_mismatch')
        attachments.append({'ordinal':index,'filename':name,'sha256':actual,'size_bytes':len(raw)})
    if cadence=='daily' and fmt!='png': raise ValueError('daily_requires_images')
    if product=='english':
        label='Markets + geopolitics'
        prefix='AGGREGATEIT · DAILY' if cadence=='daily' else 'AGGREGATEIT · WEEKLY REVIEW'
        coverage='Coverage gaps'; reviewer='Critical assessment'
    else:
        label='شؤون استراتيجية وجيوسياسية'
        prefix='أغريغيت إت · النشرة اليومية' if cadence=='daily' else 'أغريغيت إت · التقرير الأسبوعي'
        coverage='نواقص التغطية'; reviewer='اختبار الفرضية'
    parts=[f'**{prefix}** · {slot}',f'**{_single_line(headline,160)}**',label]
    parts.extend('• '+_single_line(s,210) for s in summary if s.strip())
    parts.append(reviewer+': '+_single_line(critical_review,60))
    if coverage_gaps:
        parts.append(coverage+': '+', '.join(_single_line(g,30) for g in coverage_gaps))
    parts.append('SYNTHETIC / NOT FOR DELIVERY' if product=='english' else 'اختبار تجريبي — غير مخصص للنشر')
    content='\n'.join(parts)
    if len(content)>1900: raise ValueError('message_length_exceeds_internal_budget')
    return {'schema':'aggregateit-v2-discord-preview/1','product':product,'cadence':cadence,
            'slot_id':slot,'destination_key':DESTINATIONS[product],
            'message_count':1,'format':fmt,'content':content,'attachments':attachments,
            'regions':list(regions),'coverage_gaps':list(coverage_gaps),
            'critical_review':critical_review,'can_send':False,'webhook_url':None,'synthetic':True}
