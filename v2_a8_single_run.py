"""A8: one bounded, non-publishable HTML -> evidence -> bilingual native PNG run.

This is an *isolated two-publisher validation pilot*, not an unattended
production scraper. No Discord, model, database or scheduler code is imported.
Real HTTP use requires an explicit opt-in. A dependency-injected fetcher is
supported only for deterministic tests and is identified as such in receipts.
"""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit
from v2_secure_transport import pinned_https_fetch

from v2_article_body_gate import MAX_HTML_BYTES, article_evidence, extract_body
from v2_evidence import _time, make_article, make_claim, make_event, make_excerpt
from v2_evidence_ledger import EvidenceLedger
from v2_editorial import plan_edition
from v2_native_evidence_render import render_held_editions

# Explicit approved technical test endpoints, not user-supplied arbitrary URLs.
_HOSTS = {'en-001': ('en', 'www.bbc.co.uk'), 'ar-s003': ('ar', 'www.aljazeera.net')}
_SOURCE_FIELDS = {'source_id', 'language', 'url', 'headline', 'published_at'}


def _checked_host(url: str, *, expected: str) -> str:
    if not isinstance(url, str) or len(url) > 2048:
        raise ValueError('invalid_article_url')
    try:
        p = urlsplit(url)
        host, port = p.hostname, p.port
    except ValueError as exc:
        raise ValueError('invalid_article_url') from exc
    if (p.scheme != 'https' or host != expected or port not in (None, 443)
            or p.username or p.password or p.fragment or not p.path.startswith('/news/')
            or p.query):
        # A narrow URL policy for these two specific providers.
        raise ValueError('unapproved_article_url')
    return host


def _live_html_fetch(url: str, *, timeout: int) -> dict:
    # This pilot refuses redirects, even within the original publisher host.
    return pinned_https_fetch(url,timeout=timeout,max_bytes=MAX_HTML_BYTES,
                              max_redirects=0,headers={
        'User-Agent':'AggregateIT-V2-Bounded-ReadOnly-A8/1.0',
        'Accept':'text/html'})


def run_no_post_chain(sources: list[dict], *, as_of: str, slot_id: str,
                      output_dir: Path, fetcher=None, network_opt_in: bool = False,
                      timeout: int = 8) -> dict:
    """Run both original-language products atomically without external delivery.

    Proof of collection requires network_opt_in=True and no injected fetcher.
    Returns a compact manifest, not copyrighted article-body contents.
    """
    now=_time(as_of)
    slot=_time(slot_id)
    if fetcher is None and network_opt_in is not True:
        raise ValueError('network_explicitly_disabled')
    if type(timeout) is not int or not 1<=timeout<=12:
        raise ValueError('unsafe_timeout')
    if (not isinstance(sources,list) or len(sources)!=2 or
            any(not isinstance(item,dict) or set(item)!=_SOURCE_FIELDS for item in sources)):
        raise ValueError('two_source_pilot_only')
    if {(x['source_id'], x['language']) for x in sources} != {('en-001','en'),('ar-s003','ar')}:
        raise ValueError('two_source_pilot_only')
    validated=[]
    for row in sources:
        lang,host = _HOSTS[row['source_id']]
        _checked_host(row['url'],expected=host)
        if not isinstance(row['headline'],str) or not 12<=len(row['headline'])<=300:
            raise ValueError('invalid_source_headline')
        when=_time(row['published_at'])
        age=(datetime.fromisoformat(now)-datetime.fromisoformat(when)).total_seconds()
        if age < -300 or age > 48*3600:
            raise ValueError('source_outside_recent_window')
        validated.append((row,when))
    output_dir=Path(output_dir)
    if output_dir.exists() or output_dir.is_symlink() or not output_dir.parent.is_dir() or output_dir.parent.is_symlink():
        raise ValueError('unsafe_output_destination')

    getter = fetcher if fetcher is not None else _live_html_fetch
    ledger=EvidenceLedger(max_observations=4)
    annotations=[]
    documents=[]
    for row,when in validated:
        result=getter(row['url'],timeout=timeout)
        if not isinstance(result,dict) or result.get('status')!=200:
            raise ValueError('article_http_not_200')
        if not isinstance(result.get('content_type'),str) or 'text/html' not in result['content_type'].lower():
            raise ValueError('not_html_article')
        final_url=result.get('final_url')
        try:
            _checked_host(final_url,expected=_HOSTS[row['source_id']][1])
        except ValueError as exc:
            raise ValueError('redirected_article_host') from exc
        if final_url!=row['url']:
            raise ValueError('redirected_article_host')
        raw=result.get('body')
        body=extract_body(raw,source_url=row['url'],language=row['language'])
        admitted=article_evidence(body,headline=row['headline'],published_at=when)
        source=make_article(source_id=row['source_id'],url=row['url'],original_text=body['original_text'],
                            original_language=row['language'],retrieved_at=now,published_at=when)
        position=source['original_text'].find(admitted['quote'])
        if position<0:raise ValueError('source_excerpt_not_in_revision')
        excerpt=make_excerpt(source,position,position+len(admitted['quote']))
        claim=make_claim(statement=admitted['quote'],excerpts=[excerpt])
        event=make_event(key='body-'+source['article_id'][4:],claims=[claim])
        ledger.observe(source)
        ledger.attach_excerpt(excerpt)
        ledger.attach_claim(claim)
        ledger.upsert_event(event)
        annotations.append({'event_id':event['event_id'], 'region':admitted['region'],
                            'subject_country':admitted['subject_country'],
                            'topic':admitted['topic_english'] if row['language']=='en' else admitted['topic_arabic'],
                            'priority':70})
        documents.append({'source_id':row['source_id'],'article_url':source['canonical_url'],
                          'original_language':row['language'], 'region':admitted['region'],
                          'subject_country':admitted['subject_country'],
                          'classification':admitted['classification_status'],
                          'body_sha256':body['body_sha256'],'html_sha256':body['html_sha256'],
                          'body_character_count':len(body['original_text']),
                          'source_revision_id':source['revision_id'],'excerpt_id':excerpt['excerpt_id'],
                          'excerpt_integrity_verified':excerpt['literal']==source['original_text'][position:position+len(admitted['quote'])],
                          'publisher_factual_status':'unverified_attributed'})
    english=plan_edition(ledger=ledger,annotations=annotations,product='english',slot_id=slot,as_of=now)
    arabic=plan_edition(ledger=ledger,annotations=annotations,product='arabic',slot_id=slot,as_of=now)
    if not english['selected'] or not arabic['selected']:
        raise ValueError('bilingual_publication_candidate_incomplete')
    products={p:{'selected':v['selected'],'coverage_gaps':v['missing_target_regions'],
                 'delivery_authorized':v['delivery_authorized']} for p,v in [('english',english),('arabic',arabic)]}
    transport=('injected_test_bytes' if fetcher is not None else 'explicit_live_https')
    with tempfile.TemporaryDirectory(prefix='a8-no-post-',dir=output_dir.parent) as root:
        pages_dir=Path(root)/'edition'
        rendered=render_held_editions(english,arabic,slot_id=slot,output_dir=pages_dir)
        if not isinstance(rendered,dict) or rendered.get('delivery_authorized') is not False:
            raise ValueError('rendered_delivery_not_held')
        pages=rendered['pages']
        if not isinstance(pages,list) or len(pages)!=5:
            raise ValueError('incomplete_native_page_set')
        for p in pages:
            file=pages_dir/p['path']
            if file.is_symlink() or not file.is_file() or hashlib.sha256(file.read_bytes()).hexdigest()!=p['sha256']:
                raise ValueError('native_page_integrity_failed')
        manifest={'schema':'aggregateit-v2-a8-single-run-no-post/1','as_of':now,'slot_id':slot,
                  'source_transport':transport,'live_http_performed':fetcher is None,
                  'publisher_independence_verified':False,'web_source_independence_verified':False,
                  'ledger':ledger.counters(), 'documents':documents,'products':products,'pages':pages,
                  'source_facts_verified':False,'model_called':False,'discord_sent':False,
                  'delivery_authorized':False, 'publication_rights_verified':False}
        (pages_dir/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
        os.rename(pages_dir,output_dir)  # publish the complete *local* output directory, atomically
    return manifest
