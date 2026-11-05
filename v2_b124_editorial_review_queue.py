"""B124 publisher-link-only V1/V2 disagreements for controlled analyst review.

No captured HTML, original publisher headline or article body is persisted.
Source URLs alone do not prove rights, independent factuality or materiality.
"""
from __future__ import annotations
from hashlib import sha256
from urllib.parse import urlsplit
from v2_evidence import canonical_article_url

SCHEMA='aggregateit-v2-b124-editorial-disagreement-review/1'

def build_review_queue(paired,captured_pages):
    if (not isinstance(paired,dict) or paired.get('schema')!='aggregateit-v2-b115-same-capture/1'
        or paired.get('can_release') is not False):
        raise ValueError('untrusted_b115_input')
    if not isinstance(captured_pages,list) or len(captured_pages)>64:
        raise ValueError('unbounded_review_capture')
    urls={}
    for page in captured_pages:
        if not isinstance(page,dict):raise ValueError('invalid_review_page')
        p=page.get('product')
        url=page.get('article_url')
        if p not in ('english','arabic') or not isinstance(url,str):
            raise ValueError('invalid_review_source')
        clean=canonical_article_url(url)
        parts=urlsplit(clean)
        if parts.scheme!='https' or not parts.hostname or parts.username or parts.password:
            raise ValueError('unsafe_review_source')
        identity=sha256(clean.encode('utf8')).hexdigest()
        if (p,identity) in urls and urls[(p,identity)]!=clean:
            raise ValueError('duplicate_review_identity')
        urls[(p,identity)]=clean
    rows=[]
    for product in ('english','arabic'):
        for article in paired['products'][product]['per_article']:
            selected_v1=article.get('v1_selected') is True
            selected_v2=article.get('v2_selected') is True
            if selected_v1==selected_v2:continue
            identity=article['identity_sha256']
            link=urls.get((product,identity))
            rows.append({'product':product,'identity_sha256':identity,
                         'source_url':link,
                         'v1_selected':selected_v1,'v2_selected':selected_v2,
                         'v2_decision_stage':article.get('v2_decision_stage'),
                         'v2_rejection_reason':article.get('v2_decision_reason'),
                         'v2_preselection_rank':article.get('v2_preselection_rank'),
                         'materiality':'UNASSESSED','publisher_rights':'UNVERIFIED',
                         'analyst_reviewed':False})
    rows.sort(key=lambda x:(x['product'],x['identity_sha256']))
    return {'schema':SCHEMA,'observed_at':paired['observed_at'],
            'rows':rows,'unadjudicated':len(rows),
            'missing_source_links':sum(x['source_url'] is None for x in rows),
            'content_not_archived':True,'publisher_factuality_verified':False,
            'all_differences_adequately_explained':False,'can_release':False}

def assess_analyst_reviews(queue,decisions):
    if (not isinstance(queue,dict) or queue.get('schema')!=SCHEMA
        or queue.get('can_release') is not False
        or not isinstance(decisions,list) or len(decisions)>64):
        raise ValueError('untrusted_review_inputs')
    keys={(x['product'],x['identity_sha256']) for x in queue['rows']}
    reviewed={}
    for decision in decisions:
        if not isinstance(decision,dict):raise ValueError('invalid_review')
        key=(decision.get('product'),decision.get('identity_sha256'))
        if key not in keys or key in reviewed:raise ValueError('unknown_or_duplicate_review')
        if (decision.get('materiality') not in ('material','minor','not_relevant')
            or not isinstance(decision.get('rationale'),str)
            or not 20<=len(decision['rationale'])<=1000
            or decision.get('reviewer_verified') is not True):
            raise ValueError('incomplete_analyst_adjudication')
        reviewed[key]=decision
    outstanding=sorted(k for k in keys if k not in reviewed)
    return {'schema':'aggregateit-v2-b124-editorial-human-review-status/1',
            'reviewed':len(reviewed),'outstanding':len(outstanding),
            'material_misses':sum(x.get('materiality')=='material' for x in reviewed.values()),
            'status':'HOLD_ANALYST_ADJUDICATION_REQUIRED' if outstanding else 'REVIEW_LABELS_COMPLETE_NEEDS_INDEPENDENT_CORROBORATION',
            'independent_publisher_factuality_verified':False,
            'full_model_visual_delivery_parity':False,'can_release':False}
