"""B10 source-profiled, bounded large RSS diagnostics with native-language gating.

No model, article fetching, persistence, or publication. Opt-in public HTTPS
GETs ONLY to pinned publisher feed URLs; never turn stream assignment into
verified original language or independence. All record labels are candidates.
"""
from __future__ import annotations

from datetime import datetime
import hashlib
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from v2_secure_transport import pinned_https_fetch

from v2_feed_probe import (
    MAX_BYTES, MAX_EXTENDED_BYTES, _url_safe, _assert_public_dns,
    inspect_feed_bytes, _validated_feed_byte_budget, _date
)
from v2_feed_items import extract_candidates

# Exact URL allowlist. Sizes observed in a 24 October 2026 read-only probe:
# The National 814KB, Shafaq 385KB, Dawn 346KB, Yemenat 224KB.
# Persian / Somali are included for metadata purposes, NOT Arabic admission.
_PROFILES = {
    'ar-s017': ('https://www.thenationalnews.com/arc/outboundfeeds/rss/?outputType=xml', 'gcc', 'en', 1000000),
    'ar-s026': ('https://shafaq.com/rss/ar', 'iraq', 'ar', 1000000),
    'ar-s050': ('https://www.dawn.com/feeds/home', 'pakistan', 'en', 1000000),
    'ar-s081': ('https://yemenat.net/feed', 'yemen', 'ar', 1000000),
    'ar-s019': ('https://www.irna.ir/rss', 'iran', 'fa', MAX_BYTES),
    'ar-s056': ('https://radioergo.org/feed/', 'somalia', 'so', MAX_BYTES),
}

def profile_for(source_id: str) -> dict:
    if source_id not in _PROFILES:
        raise ValueError('source_not_allowlisted')
    url, region, language, budget=_PROFILES[source_id]
    return {'source_id':source_id, 'url':url, 'region':region,
            'language':language, 'stream':'arabic', 'max_bytes':budget,
            'arabic_native':language=='ar',
            'declared_language_verification':'registry_metadata_not_linguistically_proven',
            'publisher_independence_verified':False}

def _fetch_registered_feed(url: str, *, timeout: int, max_bytes: int) -> bytes:
    _url_safe(url)
    max_bytes=_validated_feed_byte_budget(max_bytes)
    host=urlsplit(url).hostname
    packet=pinned_https_fetch(url,timeout=timeout,max_bytes=max_bytes,max_redirects=2,headers={
        'User-Agent':'AggregateIT-V2-SourceCompatibility/1.0 (read-only)',
        'Accept':'application/rss+xml,application/atom+xml,text/xml,application/xml'})
    if urlsplit(packet['final_url']).hostname!=host:
        raise ValueError('cross_origin_redirect_refused')
    if packet['status']!=200:
        raise ValueError('non_200_feed')
    mime=packet['content_type'].split(';',1)[0].lower().strip()
    if mime not in ('application/rss+xml','application/atom+xml','application/xml','text/xml'):
        raise ValueError('not_xml_content_type')
    return packet['body']

def _script_fit(items: list[dict], *, language: str) -> bool:
    if not items:
        return False
    sample=' '.join(v['title'] for v in items[:12])
    arabic=len(re.findall(r'[\u0600-\u06ff]',sample))
    latin=len(re.findall(r'[A-Za-z]',sample))
    letters=arabic+latin
    if not letters:
        return False
    if language in ('ar','fa'):
        return arabic/letters>=.6
    if language in ('en','so'):
        return latin/letters>=.6
    return False

def probe_regional_source(source_id: str, *, now: str, fetcher=None,
                          network_opt_in: bool=False, timeout: int=8) -> dict:
    """Metadata audit, never editorial or commercial source admission."""
    profile=profile_for(source_id)
    if _date(now) is None:raise ValueError('timezone_required')
    if type(timeout) is not int or not 1<=timeout<=12:raise ValueError('unsafe_timeout')
    if fetcher is None and not network_opt_in:
        raise ValueError('network_opt_in_required')
    result={'schema':'aggregateit-v2-b10-source-observation/1',**profile,
            'status':'unprobed','candidate_count':0,'recent_count':0,
            'arabic_original_language_candidate':False,
            'live_http_performed':False, 'model_called':False,
            'publication_rights_verified':False, 'source_truth_verified':False,
            'delivery_authorized':False, 'article_bodies_retained':False}
    try:
        if fetcher is None:
            raw=_fetch_registered_feed(profile['url'],timeout=timeout,max_bytes=profile['max_bytes'])
            result['live_http_performed']=True
        else:
            raw=fetcher(profile['url'],timeout=timeout)
    except HTTPError as exc:
        result['status']=f'http_{exc.code}'
        return result
    except (OSError,URLError,TimeoutError):
        result['status']='network_error'
        return result
    except ValueError as exc:
        result['status']=str(exc) if str(exc) in (
            'cross_origin_redirect_refused','not_xml_content_type','unsafe_resolved_ip','non_200_feed') else 'invalid_response'
        return result

    if not isinstance(raw,bytes):
        result['status']='invalid_payload_type'
        return result
    result['response_bytes']=len(raw)
    if len(raw)>profile['max_bytes']:
        result['status']='oversized_body'
        return result
    result['response_sha256']=hashlib.sha256(raw).hexdigest()
    health=inspect_feed_bytes(raw,now=now,max_bytes=profile['max_bytes'])
    result['status']=health['status']
    result['recent_count']=health['recent_count']
    result['entry_count']=health['entry_count']
    result['newest_item_at']=health['newest_item_at']
    if health['status']!='usable_dated_feed':
        return result
    rows=extract_candidates(raw,feed_url=profile['url'],observed_at=now,
                            max_items=20,max_bytes=profile['max_bytes'])
    result['candidate_count']=rows['candidate_count']
    if not _script_fit(rows['items'],language=profile['language']):
        result['status']='script_mismatch'
        result['candidate_count']=0
        return result
    result['arabic_original_language_candidate']=profile['language']=='ar' and rows['candidate_count']>0
    return result
