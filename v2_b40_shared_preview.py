"""B40 continuation: genuine same-buffer V1/V2 headline *preview* comparison.

NOT a full editorial, model, translation, native Gazette or Discord comparison.
Only hashed/count summary may leave the runner. Original RSS remains in memory.
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from hashlib import sha256
from html import unescape
import json
import re
from v2_b31_same_input_shadow import _english_v1, _arabic_v1, _fingerprint, _verified_v1_code
from v2_b37_mobile_headlines import render_source_watch_html
from v2_feed_items import extract_candidates
from v2_feed_probe import _date, _url_safe

def _v1_rows(raw: bytes, product: str, feed_url: str, now: datetime):
    if product == 'english':
        return asyncio.run(_english_v1(raw, feed_url, now))
    return _arabic_v1(raw, feed_url)

def compare_previews(raw: bytes, *, product: str, feed_url: str, observed_at: str):
    if product not in ('english','arabic') or not isinstance(raw,bytes) or not 1<=len(raw)<=1_000_000:
        raise ValueError('invalid_exact_capture')
    _url_safe(feed_url)
    now=_date(observed_at)
    if now is None:raise ValueError('invalid_observation_window')
    if not _verified_v1_code():raise ValueError('legacy_parser_drift')
    cap=5 if product=='english' else 35
    previous=_v1_rows(raw,product,feed_url,now)
    v2=extract_candidates(raw,feed_url=feed_url,observed_at=now.isoformat(),
                          max_items=cap,max_age_hours=72,max_bytes=1_000_000)
    normalized_v1=[]
    for row in previous:
        if not isinstance(row,dict):continue
        raw_time=row.get('ts') if product=='english' else row.get('published')
        if not isinstance(raw_time,(float,int)) or isinstance(raw_time,bool):continue
        try:
            dt=datetime.fromtimestamp(raw_time,tz=timezone.utc)
            if not -300 <= (now-dt).total_seconds() <= 72*3600:continue
            url=row.get('url')
            _url_safe(url)
        except (OverflowError,OSError,TypeError,ValueError):
            continue
        title=row.get('title')
        if not isinstance(title,str) or not 5<=len(title.strip())<=300:continue
        normalized_v1.append({'article_url':url,'title':re.sub(r'\s+',' ',unescape(title)).strip(),
                              'source_feed_url':feed_url,'published_at':dt.isoformat()})
    a={_fingerprint(r['article_url'],r['title'],_date(r['published_at'])) for r in normalized_v1}
    b={_fingerprint(r['article_url'],r['title'],_date(r['published_at'])) for r in v2['items']}
    html_a=render_source_watch_html(product,normalized_v1,now.isoformat(),max_items=6)
    html_b=render_source_watch_html(product,v2['items'],now.isoformat(),max_items=6)
    return {'schema':'aggregateit-v2-b40-shared-input-headline-preview/1',
            'product':product,'capture_sha256':sha256(raw).hexdigest(),'capture_size_bytes':len(raw),
            'observed_at':now.isoformat(),'v1_reference_blob_verified':True,
            'v1_eligible':len(a),'v2_eligible':len(b),'matching_count':len(a&b),
            'v1_only_count':len(a-b),'v2_only_count':len(b-a),
            'identity_parity':a==b,
            'v1_source_headline_cards':html_a['shown'],
            'v2_source_headline_cards':html_b['shown'],
            'source_only_markup_equal':sha256(html_a['html'].encode('utf8')).digest()==sha256(html_b['html'].encode('utf8')).digest(),
            'v1_preview_sha256':sha256(html_a['html'].encode('utf8')).hexdigest(),
            'v2_preview_sha256':sha256(html_b['html'].encode('utf8')).hexdigest(),
            'real_article_body_verified':False,'editorial_selection_comparable':False,
            'llm_or_translation_comparable':False,'native_page_equivalence':False,
            'external_delivery_comparable':False,'no_raw_source_artifact':True,
            'can_send':False,'discord_sent':False}
