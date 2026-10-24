"""Source-gated RSS/Atom item extraction; never admits headlines as verified facts.

Read-only pure parser for a bounded single RSS response, not a crawler.
The returned items are candidate observations requiring article-level evidence.
"""
from __future__ import annotations
import hashlib
import html
import re
from xml.etree import ElementTree as ET

from v2_feed_probe import MAX_BYTES, _date, _url_safe, _reject_dtd, _validated_feed_byte_budget


def _text(element, local_name: str) -> str:
    for child in element:
        if child.tag.rsplit('}', 1)[-1].lower() == local_name:
            return ' '.join(''.join(child.itertext()).split())
    return ''


def _atom_link(element) -> str:
    for child in element:
        if child.tag.rsplit('}',1)[-1] == 'link' and child.attrib.get('rel','alternate') == 'alternate':
            return child.attrib.get('href','').strip()
    return ''


def extract_candidates(feed_bytes: bytes, *, feed_url: str, observed_at: str,
                       max_age_hours: int=72, max_items: int=30,
                       max_bytes: int=MAX_BYTES) -> dict:
    _url_safe(feed_url)
    _validated_feed_byte_budget(max_bytes)
    now=_date(observed_at)
    if now is None: raise ValueError('timezone_required')
    if type(max_items) is not int or not 1<=max_items<=50: raise ValueError('invalid_item_budget')
    if type(max_age_hours) is not int or not 1<=max_age_hours<=168: raise ValueError('invalid_freshness_window')
    if not isinstance(feed_bytes, bytes) or len(feed_bytes)>max_bytes:
        raise ValueError('invalid_feed_payload')
    if _reject_dtd(feed_bytes):
        raise ValueError('invalid_feed_xml')
    try: root=ET.fromstring(feed_bytes)
    except ET.ParseError as exc: raise ValueError('invalid_feed_xml') from exc
    kind=root.tag.rsplit('}',1)[-1].lower()
    if kind=='rss':
        candidates=root.findall('./channel/item')
    elif kind=='feed':
        candidates=[e for e in root if e.tag.rsplit('}',1)[-1].lower()=='entry']
    elif kind=='rdf':
        candidates=[e for e in root if e.tag.rsplit('}',1)[-1].lower()=='item']
    else:
        raise ValueError('unsupported_feed_root')
    rows=[];seen=set()
    rejected={'missing_title':0,'invalid_link':0,'missing_or_stale_date':0,'duplicate_link':0,'over_budget':0}
    for entry in candidates:
        title=html.unescape(_text(entry,'title'))
        title=re.sub(r'\s+',' ',title).strip()
        if not 5<=len(title)<=300:
            rejected['missing_title']+=1;continue
        link=_atom_link(entry) if kind=='feed' else _text(entry,'link')
        if not link:
            rejected['invalid_link']+=1;continue
        try: _url_safe(link)
        except ValueError:
            rejected['invalid_link']+=1;continue
        stamp=(_text(entry,'published') or _text(entry,'updated') or
               _text(entry,'pubdate') or _text(entry,'date'))
        date=_date(stamp)
        if date is None or not -300 <= (now-date).total_seconds() <= max_age_hours*3600:
            rejected['missing_or_stale_date']+=1;continue
        if link in seen:
            rejected['duplicate_link']+=1;continue
        seen.add(link)
        if len(rows)>=max_items:
            rejected['over_budget']+=1;continue
        rows.append({
            'candidate_id':'fc_'+hashlib.sha256((feed_url+'|'+link).encode('utf8')).hexdigest()[:24],
            'source_feed_url':feed_url,
            'article_url':link,'title':title,
            'published_at':date.isoformat(),'observed_at':now.isoformat(),
            'declared_language':'unverified',
            'publisher_family':'unverified',
            'article_body_observed':False,
            'verified_claims':0,
            'editorial_admission':'held_pending_article_evidence'
        })
    return {'schema':'aggregateit-v2-feed-candidates/1',
            'feed_url':feed_url,'observed_at':now.isoformat(),
            'candidate_count':len(rows),'items':rows,
            'rejected':rejected,'independent_publishers_verified':0,
            'live_extraction_validated':False,'can_publish':False}
