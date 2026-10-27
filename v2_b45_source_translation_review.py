"""B45: fail-closed source-bound translation validation; never a live model claim."""
from __future__ import annotations
from collections import Counter
from hashlib import sha256
from urllib.parse import urlsplit
import re
from arabic_live_v2 import _normalize_translations

def samples_for_source(row,articles,max_samples=2):
    if row.get('enabled') is not False or max_samples not in (1,2,3):
        raise ValueError('not_disabled_or_invalid_budget')
    selected=[]
    for item in articles:
        if len(selected)>=max_samples:break
        if item.get('source_id')!=row['id'] or item.get('language')!=row['language']:
            raise ValueError('source_alignment_error')
        title=item.get('title','')
        summary=item.get('text') or title
        url=item.get('url','')
        p=urlsplit(url)
        if p.scheme!='https' or not p.hostname or not isinstance(title,str) or len(title)<5:
            continue
        source={'source_id':row['id'],'language':row['language'],
                'title':title[:220],'summary':summary[:900],'url':url}
        source['source_sha256']=sha256((source['source_id']+'\n'+url+'\n'+source['title']+
                                       '\n'+source['summary']).encode('utf8')).hexdigest()
        selected.append(source)
    return selected

def _digits(text):
    t=text.translate(str.maketrans('٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹','01234567890123456789'))
    return Counter(re.findall(r'\d+(?:[.,]\d+)*',t))

def inspect_translations(samples,proposals):
    if not isinstance(samples,list) or len(samples)>20 or not isinstance(proposals,dict):
        raise ValueError('invalid_translation_batch')
    translated=proposals.get('items')
    if not isinstance(translated,list):raise ValueError('invalid_model_output')
    accepted=[];failures=[];seen=set()
    for proposal in translated:
        if not isinstance(proposal,dict) or type(proposal.get('index')) is not int:
            failures.append('bad_index');continue
        i=proposal['index']
        if i<0 or i>=len(samples) or i in seen:
            failures.append('duplicate_or_unbound_index');continue
        seen.add(i)
        original=samples[i]
        if proposal.get('source_sha256')!=original.get('source_sha256'):
            failures.append('source_digest_changed');continue
        mapped=_normalize_translations({'items':[{**proposal,'index':0}]},[original])
        if 0 not in mapped:
            failures.append('production_validator_rejected');continue
        output=mapped[0]['title_ar']+' '+mapped[0]['summary_ar']
        source=original['title']+' '+original['summary']
        if _digits(output)!=_digits(source):
            failures.append('quantity_multiset_changed');continue
        arabic=sum('\u0600'<=c<='\u06ff' for c in output)
        latin=sum('a'<=c.lower()<='z' for c in output)
        if arabic/max(1,arabic+latin)<0.6:
            failures.append('insufficient_arabic');continue
        accepted.append({'source_id':original['source_id'],'source_sha256':original['source_sha256'],
                         'ready_for_semantic_review':True,'publishable':False})
    failures.extend(['missing_translation']*(len(samples)-len(seen)))
    return {'schema':'aggregateit-v2-b45-source-bound-review/1','samples':len(samples),
            'structural_review_passed':len(accepted),'review':accepted,
            'reasons':dict(Counter(failures)),
            'live_provider_called':False,'semantic_translation_verified':False,
            'can_release':False}

def pending_summary(samples):
    return {'schema':'aggregateit-v2-b45-pending-live-translation/1',
            'sample_count':len(samples),'languages':dict(Counter(s['language'] for s in samples)),
            'provider_translation_verified':False,'somali_arabic_quality_verified':False,
            'english_arabic_quality_verified':False,'can_release':False}
