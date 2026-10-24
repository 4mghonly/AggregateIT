"""Bounded read-only BBC/Al Jazeera HTML article-body evidence gate.

Strictly a content parser and limited deterministic country classifier, not a
network client or a truth/veracity verifier. No arbitrary location guessing.
"""
from __future__ import annotations

from datetime import datetime
from hashlib import sha256
from html.parser import HTMLParser
from urllib.parse import urlsplit
import re

MAX_HTML_BYTES=850_000
MAX_BODY_CHARS=32_000
MIN_BODY_CHARS=80
_MAX_QUOTE_CHARS=190
_MAX_QUOTE_WORDS=25
_ALLOWED_HOSTS={'www.bbc.co.uk':'article_element','www.bbc.com':'article_element',
                'www.aljazeera.net':'aljazeera_article_wysiwyg'}
_BLOCK_TAGS={'script','style','noscript','nav','footer','header','aside','button','form'}
_COUNTRIES=(
 ('jordan','JO', r'\bJordan(?:ian)?\b',r'الأردن|أردني(?:ون|ين|ة)?|الأردنية|الكرك'),
 ('yemen','YE',r'\bYemen(?:i)?\b',r'اليمن|يمني(?:ين|ون|ة)?'),
 ('gcc','AE',r'\b(?:UAE|United Arab Emirates|Emirati)\b',r'الإمارات|إماراتي(?:ة|ين)?'),
 ('iran','IR',r'\bIran(?:ian)?\b',r'إيران|إيراني(?:ة|ون|ين)?'),
 ('iraq','IQ',r'\bIraq(?:i)?\b',r'العراق|عراقي(?:ة|ون|ين)?'),
 ('sudan','SD',r'\bSudan(?:ese)?\b',r'السودان|سوداني(?:ة|ين)?'),
 ('somalia','SO',r'\bSomali(?:a|an)?\b',r'الصومال|صومالي(?:ة|ين)?'),
 ('pakistan','PK',r'\bPakistan(?:i)?\b',r'باكستان|باكستاني(?:ة|ين)?'),
 ('afghanistan','AF',r'\bAfghanistan|\bAfghan\b',r'أفغانستان|أفغاني(?:ة|ين)?'),
 ('turkey','TR',r'\bTurk(?:ey|ish|iye)\b',r'تركيا|تركي(?:ة|ين)?'),
 ('egypt','EG',r'\bEgypt(?:ian)?\b',r'مصر|مصري(?:ة|ين)?'),
)

class _ArticleParser(HTMLParser):
    def __init__(self,basis):
        super().__init__(convert_charrefs=True)
        self.basis=basis;self.stack=[];self.current=None;self.paragraphs=[]
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        classes=set(attrs.get('class','').split())
        valid_article=(tag=='article') if self.basis=='article_element' else (tag=='div' and 'wysiwyg--all-content' in classes)
        self.stack.append((tag,valid_article))
        if tag=='p' and self.current is None and self._body_visible():self.current=[]
    def _body_visible(self):
        return any(flag for _,flag in self.stack) and not any(tag in _BLOCK_TAGS for tag,_ in self.stack)
    def handle_endtag(self,tag):
        if tag=='p' and self.current is not None:
            txt=' '.join(''.join(self.current).split())
            if 25 <= len(txt) <= 3500 and txt.lower() not in {'this video can not be played', 'this video cannot be played'}:
                self.paragraphs.append(txt)
            self.current=None
        for i in range(len(self.stack)-1,-1,-1):
            if self.stack[i][0]==tag:
                self.stack=self.stack[:i];break
    def handle_data(self,data):
        if self.current is not None and self._body_visible():self.current.append(data)

def extract_body(html_bytes:bytes,*,source_url:str,language:str)->dict:
    if not isinstance(html_bytes,bytes) or not 0<len(html_bytes)<=MAX_HTML_BYTES:
        raise ValueError('html_size_out_of_bounds')
    try:host=urlsplit(source_url).hostname
    except (ValueError,TypeError):host=None
    if (not isinstance(source_url,str) or not source_url.startswith('https://') or
            host not in _ALLOWED_HOSTS or language not in ('en','ar')):
        raise ValueError('unapproved_article_source')
    basis=_ALLOWED_HOSTS[host]
    parser=_ArticleParser(basis)
    parser.feed(html_bytes.decode('utf-8',errors='replace'))
    paragraphs=parser.paragraphs
    if len(paragraphs)<2:
        raise ValueError('article_body_container_missing')
    body='\n\n'.join(paragraphs)
    if not MIN_BODY_CHARS<=len(body)<=MAX_BODY_CHARS:raise ValueError('article_body_length_out_of_bounds')
    arabic=len(re.findall(r'[\u0600-\u06ff]',body))
    letters=len(re.findall(r'[A-Za-z\u0600-\u06ff]',body))
    if not letters or (arabic/letters<.35 if language=='ar' else arabic/letters>.2):
        raise ValueError('body_script_mismatch')
    return {'schema':'aggregateit-v2-article-body/1','source_url':source_url,
            'original_language':language,'extraction_basis':basis,'paragraphs':paragraphs,
            'original_text':body,'body_sha256':sha256(body.encode('utf-8')).hexdigest(),
            'html_sha256':sha256(html_bytes).hexdigest(),'html_bytes':len(html_bytes),
            'article_authorized_for_publication':False}

def classify_geography(headline:str,body:str,*,language:str)->dict:
    if not all(isinstance(v,str) and v for v in (headline,body)) or language not in ('en','ar'):
        raise ValueError('no_grounded_region')
    idx=2 if language=='en' else 3
    matches=[(reg,ctry) for reg,ctry,*patterns in _COUNTRIES if re.search(patterns[idx-2],headline,re.I)]
    if not matches:raise ValueError('no_grounded_region')
    if len(matches)!=1:raise ValueError('ambiguous_geography')
    region,country=matches[0]
    region_rule=next(x for x in _COUNTRIES if x[0]==region)
    if not re.search(region_rule[idx],body,re.I):raise ValueError('country_not_supported_by_article_body')
    if language=='en':
        if re.search(r'\b(?:attack|shoot|kill|killed|dead|gunmen|security|military)\b',headline,re.I):topic='security'
        else:topic='geopolitics'
    else:
        if re.search(r'هجوم|قتلى|قتل|إصابة|أمني|عسكري|رصاص|كنيسة',headline):topic='security'
        elif re.search(r'دبلوماس|مباحثات|وزير|زيارة رسمية',headline):topic='diplomacy'
        else:raise ValueError('arabic_topic_without_explicit_trigger')
    return {'region':region,'subject_country':country,
            'topic_english':topic if language=='en' else None,
            'topic_arabic':topic if language=='ar' else None,
            'classification_status':'headline_and_body_explicit_country',
            'classification_method':'bounded_exact_country_lexicon',
            'event_truth_verified':False}

def article_evidence(body:dict,*,headline:str,published_at:str)->dict:
    if not isinstance(body,dict) or body.get('schema')!='aggregateit-v2-article-body/1':
        raise ValueError('body_evidence_required')
    try:stamp=datetime.fromisoformat(published_at.replace('Z','+00:00'))
    except (ValueError,AttributeError):raise ValueError('publication_timestamp_required') from None
    if stamp.utcoffset() is None:raise ValueError('publication_timestamp_required')
    geo=classify_geography(headline,body['original_text'],language=body['original_language'])
    rule=next(x for x in _COUNTRIES if x[0]==geo['region'])
    geography_pattern=rule[2] if body['original_language']=='en' else rule[3]
    for paragraph in body['paragraphs']:
        if len(paragraph)<60 or not re.search(geography_pattern,paragraph,re.I):
            continue
        words=paragraph.split()
        if len(words)<5:continue
        selected=' '.join(words[:_MAX_QUOTE_WORDS])
        while len(selected)>_MAX_QUOTE_CHARS and len(selected.split())>1:
            selected=' '.join(selected.split()[:-1])
        if len(selected)>=35:
            break
    else:raise ValueError('no_short_attributed_excerpt')
    if selected not in body['original_text']:
        raise ValueError('excerpt_integrity_failed')
    return {'quote':selected,'headline':headline,'source_url':body['source_url'],
            'language':body['original_language'],'published_at':stamp.isoformat(),
            'html_sha256':body['html_sha256'],'body_sha256':body['body_sha256'],
            'extraction_basis':body['extraction_basis'],'publisher_factual_status':'unverified_attributed',
            **geo}
