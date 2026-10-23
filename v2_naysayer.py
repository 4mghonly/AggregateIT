"""Offline evidence-gated bilingual Naysayer candidate validator.

This component does not call a model, read external sources, write storage, or
publish. It validates references and *external* language/operator attestations;
it cannot establish the truth of a generated interpretation. Every result
remains non-publishable pending editorial and real-source checks.
"""
from __future__ import annotations

from datetime import datetime, timezone
from copy import deepcopy

PRODUCT_LANG = {'english':'en', 'arabic':'ar'}
CADENCES = {'daily','weekly'}
ALLOWED_STATUS = {'supported_challenge','assessment_survives','insufficient_evidence','withheld'}
FIELDS = frozenset({
    'product', 'cadence', 'slot_id', 'review_status', 'target_event_id',
    'target_claim_id', 'lead_assessment', 'challenge', 'evidence_for',
    'evidence_against', 'critical_assumptions', 'what_would_change_the_assessment',
    'weekly_change', 'translation_provenance',
})


def _date(text):
    if not isinstance(text,str):
        raise ValueError('invalid_timestamp')
    try:
        dt=datetime.fromisoformat(text.replace('Z','+00:00'))
    except ValueError as exc:
        raise ValueError('invalid_timestamp') from exc
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError('timezone_required')
    return dt.astimezone(timezone.utc)


def _notice(product, cadence, slot_id, status='insufficient_evidence', reason='no_review_candidate'):
    return {
        'schema':'aggregateit-naysayer-review/1',
        'product':product,'language':PRODUCT_LANG[product],
        'cadence':cadence,'slot_id':slot_id,
        'review_status':status,'reason':reason,'visible':True,
        'title':('Critical assessment' if product=='english' else 'اختبار الفرضية'),
        'lead_assessment':'','challenge':'',
        'cited_evidence':[], 'independent_operator_count':0,
        'critical_assumptions':[], 'what_would_change_the_assessment':[],
        'weekly_change':'', 'target_event_id':'', 'target_claim_id':'',
        'editorial_disposition':'abstain',
        'factual_accuracy_verified':False,'delivery_authorized':False,
    }


def _check_text(s, *, allow_empty=False, max_chars=3000):
    return isinstance(s, str) and len(s)<=max_chars and (allow_empty or bool(s.strip()))


def _source_evidence(ledger, excerpt_id, allowed_ids, families, languages, language, as_of, max_age_hours):
    if not isinstance(excerpt_id,str) or excerpt_id not in allowed_ids:
        return None,'unlinked_excerpt'
    excerpt=ledger._excerpts.get(excerpt_id)
    if not isinstance(excerpt,dict):
        return None,'unlinked_excerpt'
    src=excerpt.get('source_id');rev=excerpt.get('revision_id')
    record=ledger._source_revisions.get((src,rev))
    if not record or not excerpt.get('article_id') or not src:
        return None,'unlinked_excerpt'
    if languages.get(excerpt_id)!=language or excerpt.get('original_language','').split('-')[0]!=language:
        return None,'source_language_unverified'
    family=families.get(src)
    if not isinstance(family,str) or not family.strip() or family.lower() in ('unknown','unverified','none'):
        return None,'unverified_publisher_family'
    stamp=record.get('published_at') or record.get('retrieved_at')
    try:
        age_hours=(as_of-_date(stamp)).total_seconds()/3600
    except ValueError:
        return None,'undated_evidence'
    if age_hours < -5/60 or age_hours>max_age_hours:
        return None,'stale_evidence'
    if not isinstance(excerpt.get('article_id'),str):
        return None,'unlinked_excerpt'
    return {'excerpt_id':excerpt_id,'source_id':src,'article_id':excerpt['article_id'],
            'operator_family_id':family,'language':language},None


def build_review(proposal, *, ledger, as_of, verified_families, verified_languages,
                 product=None, cadence=None, slot_id=None):
    """Validate an untrusted proposal against an existing B3 ledger.

    verified_families/verified_languages must be independently obtained. They
    must NEVER be populated from the proposal or from feed labels alone.
    """
    if proposal is not None and isinstance(proposal,dict):
        product=product or proposal.get('product')
        cadence=cadence or proposal.get('cadence')
        slot_id=slot_id or proposal.get('slot_id')
    if product not in PRODUCT_LANG or cadence not in CADENCES:
        raise ValueError('invalid_review_target')
    _date(as_of);_date(slot_id)
    if proposal is None:
        return _notice(product,cadence,slot_id)
    def withheld(reason):
        return _notice(product,cadence,slot_id,'withheld',reason)
    if not isinstance(proposal,dict) or set(proposal)!=FIELDS:
        return withheld('invalid_review_schema')
    if proposal['product']!=product or proposal['cadence']!=cadence or proposal['slot_id']!=slot_id:
        return withheld('review_target_mismatch')
    status=proposal['review_status']
    if not isinstance(status,str) or status not in ALLOWED_STATUS:
        return withheld('invalid_review_status')
    if status in ('withheld','insufficient_evidence'):
        return _notice(product,cadence,slot_id,status,'reviewer_abstained')
    for key in ('lead_assessment','challenge','weekly_change'):
        if not _check_text(proposal[key],allow_empty=key!='lead_assessment',max_chars=3000):
            return withheld('invalid_review_text')
    for key in ('critical_assumptions','what_would_change_the_assessment'):
        v=proposal[key]
        if not isinstance(v,list) or len(v)>6 or any(not _check_text(s,max_chars=200) for s in v):
            return withheld('invalid_review_indicators')
    if proposal['translation_provenance']!='original':
        return withheld('translation_unverified')
    budget=(110 if product=='english' else 95) if cadence=='daily' else (550 if product=='english' else 450)
    words=len((proposal['lead_assessment']+' '+proposal['challenge']).split())
    if words>budget:
        return withheld('word_budget_exceeded')
    if cadence=='weekly' and not proposal['weekly_change'].strip():
        return withheld('weekly_delta_missing')
    try:
        history=ledger._events.get(proposal['target_event_id'],[])
        claims=history[-1]['claim_ids'] if history else []
    except (TypeError,KeyError,IndexError):
        claims=[]
    if proposal['target_claim_id'] not in claims:
        return withheld('unlinked_claim')
    if not isinstance(proposal['evidence_for'],list) or not isinstance(proposal['evidence_against'],list):
        return withheld('invalid_review_evidence')
    if len(proposal['evidence_for'])>8 or len(proposal['evidence_against'])>8:
        return withheld('evidence_budget_exceeded')
    if not proposal['evidence_for']:
        return withheld('missing_lead_evidence')
    if status=='supported_challenge' and (not proposal['evidence_against'] or not proposal['challenge'].strip()):
        return withheld('missing_challenge_evidence')
    if status=='assessment_survives' and proposal['evidence_against']:
        return withheld('contested_assessment_requires_review')
    try:
        allowed_ids=set().union(*(set(ledger._claims[c]['excerpt_ids']) for c in claims))
    except (KeyError,TypeError):
        return withheld('unlinked_claim')
    if any(not isinstance(ex,str) or ex not in allowed_ids for ex in proposal['evidence_for']+proposal['evidence_against']):
        return withheld('unlinked_excerpt')
    lang=PRODUCT_LANG[product];now=_date(as_of);max_age=72 if cadence=='daily' else 21*24
    citations=[];seen=set();family_for=set();family_against=set()
    for side in ('for','against'):
        for ex in proposal['evidence_'+side]:
            if ex in seen:
                return withheld('duplicate_evidence')
            seen.add(ex)
            row,reason=_source_evidence(ledger,ex,allowed_ids,verified_families,
                                        verified_languages,lang,now,max_age)
            if reason:
                return withheld(reason)
            citations.append(dict(row,side=side))
            (family_for if side=='for' else family_against).add(row['operator_family_id'])
    if status=='supported_challenge' and len(family_for|family_against)<2:
        return withheld('no_independent_challenge_evidence')
    if status=='supported_challenge' and not family_against.difference(family_for):
        return withheld('no_independent_challenge_evidence')
    r=_notice(product,cadence,slot_id,status,'evidence_links_checked_content_unverified')
    r.update(lead_assessment=proposal['lead_assessment'],challenge=proposal['challenge'],
             target_event_id=proposal['target_event_id'],target_claim_id=proposal['target_claim_id'],
             cited_evidence=citations,independent_operator_count=len(family_for|family_against),
             critical_assumptions=deepcopy(proposal['critical_assumptions']),
             what_would_change_the_assessment=deepcopy(proposal['what_would_change_the_assessment']),
             weekly_change=proposal['weekly_change'],
             editorial_disposition=('qualify' if status=='supported_challenge' else 'retain'))
    return r


def build_report(proposals, *, ledger, as_of, verified_families, verified_languages,
                 product, cadence, slot_id):
    if product not in PRODUCT_LANG or cadence not in CADENCES:
        raise ValueError('invalid_report_target')
    _date(as_of);_date(slot_id)
    if not isinstance(proposals,list) or len(proposals)>5:
        raise ValueError('review_batch_ceiling')
    if cadence=='daily':
        if len(proposals)>1:
            return {'schema':'aggregateit-naysayer-report/1','product':product,
                    'cadence':cadence,'slot_id':slot_id,'sections':[],
                    'quality_gate_passed':False,'reason':'daily_exactly_one_review',
                    'delivery_authorized':False}
        sections=[build_review(proposals[0] if proposals else None,ledger=ledger,
                               as_of=as_of,verified_families=verified_families,
                               verified_languages=verified_languages,product=product,
                               cadence=cadence,slot_id=slot_id)]
        gate=sections[0]['review_status'] in ('supported_challenge','assessment_survives')
        reason='candidate_evidence_links_only' if gate else 'visible_degraded_notice_only'
    else:
        sections=[build_review(p,ledger=ledger,as_of=as_of,
                               verified_families=verified_families,verified_languages=verified_languages,
                               product=product,cadence=cadence,slot_id=slot_id)
                  for p in proposals]
        event_ids=[p['target_event_id'] for p in sections if p['target_event_id']]
        gate=3<=len(sections)<=5 and len(set(event_ids))==len(sections)
        reason='candidate_evidence_links_only' if gate else 'weekly_needs_three_distinct_reviews'
    return {'schema':'aggregateit-naysayer-report/1','product':product,
            'cadence':cadence,'slot_id':slot_id,'sections':sections,
            'quality_gate_passed':gate,'reason':reason,'delivery_authorized':False}
