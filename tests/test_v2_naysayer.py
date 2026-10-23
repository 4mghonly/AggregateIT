"""Synthetic, zero-egress English/Arabic daily and weekly Naysayer checks."""
import copy
import unittest
from v2_naysayer import build_review, build_report

NOW = '2026-10-24T03:00:00+04:00'
SLOT = '2026-10-24T06:00:00+04:00'

class FakeLedger:
    def __init__(self):
        self._events={'evt_valid':[{'event_id':'evt_valid','claim_ids':['claim_lead','claim_against']}]} 
        self._claims={
            'claim_lead':{'kind':'publisher_assertion','excerpt_ids':['exc_1']},
            'claim_against':{'kind':'publisher_assertion','excerpt_ids':['exc_2']}
        }
        self._excerpts={
            'exc_1': {'excerpt_id':'exc_1','source_id':'src1','revision_id':'rev1','article_id':'article1','original_language':'en','literal':'A verified synthetic statement.'},
            'exc_2': {'excerpt_id':'exc_2','source_id':'src2','revision_id':'rev2','article_id':'article2','original_language':'en','literal':'Another attributed synthetic report.'}
        }
        self._source_revisions={
            ('src1','rev1'):{'published_at':'2026-10-23T03:00:00+04:00','retrieved_at':'2026-10-23T03:00:00+04:00'},
            ('src2','rev2'):{'published_at':'2026-10-23T03:00:00+04:00','retrieved_at':'2026-10-23T03:00:00+04:00'}
        }

class CriticTests(unittest.TestCase):
    def setUp(self):
        self.l=FakeLedger()
        self.fam={'src1':'operator_A','src2':'operator_B'}
        self.lang={'exc_1':'en','exc_2':'en'}
        self.p={'product':'english','cadence':'daily','slot_id':SLOT,'review_status':'supported_challenge',
                'target_event_id':'evt_valid','target_claim_id':'claim_lead',
                'lead_assessment':'This synthetic incident might be escalating.',
                'challenge':'The available synthetic reports also allow a less severe interpretation.',
                'evidence_for':['exc_1'],'evidence_against':['exc_2'],
                'critical_assumptions':['Both reports concern the same time window'],
                'what_would_change_the_assessment':['New primary observations'],
                'weekly_change':'','translation_provenance':'original'}
    def go(self,p=None,**overrides):
        return build_review(p or self.p,ledger=self.l,as_of=NOW,
                            verified_families=overrides.get('families',self.fam),
                            verified_languages=overrides.get('languages',self.lang))
    def test_supported_challenge_has_citations_and_never_claims_live_publication(self):
        r=self.go()
        self.assertEqual(r['review_status'],'supported_challenge')
        self.assertEqual(len(r['cited_evidence']),2)
        self.assertFalse(r['delivery_authorized'])
        self.assertTrue(r['visible'])
        self.assertEqual(r['independent_operator_count'],2)
    def test_missing_family_fails_instead_of_claiming_independent_confirmation(self):
        r=self.go(families={'src1':'operator_A'})
        self.assertEqual(r['review_status'],'withheld')
        self.assertEqual(r['reason'],'unverified_publisher_family')
    def test_syndicated_mirrors_not_counted_as_distinct_origins(self):
        r=self.go(families={'src1':'same','src2':'same'})
        self.assertEqual(r['review_status'],'withheld')
        self.assertEqual(r['reason'],'no_independent_challenge_evidence')
    def test_unknown_excerpt_fails_closed(self):
        p=copy.deepcopy(self.p)
        p['evidence_against']=['exc_missing']
        r=self.go(p)
        self.assertEqual(r['review_status'],'withheld')
        self.assertEqual(r['reason'],'unlinked_excerpt')
    def test_external_claim_not_allowed_as_event_evidence(self):
        self.l._excerpts['exc_unrelated']={'source_id':'src2','revision_id':'rev2','article_id':'article2','original_language':'en'}
        p=copy.deepcopy(self.p);p['evidence_against']=['exc_unrelated']
        self.assertEqual(self.go(p)['review_status'],'withheld')
    def test_arabic_not_assumed_from_script(self):
        p=copy.deepcopy(self.p)
        p.update(product='arabic',lead_assessment='هذا تحليل افتراضي',challenge='هذا نقد افتراضي')
        self.assertEqual(self.go(p)['reason'],'source_language_unverified')
    def test_no_evidence_returns_visible_insufficient_notice(self):
        r=build_review(None,ledger=self.l,as_of=NOW,verified_families={},verified_languages={},
                       product='arabic',cadence='daily',slot_id=SLOT)
        self.assertEqual(r['review_status'],'insufficient_evidence')
        self.assertTrue(r['visible'])
        self.assertFalse(r['delivery_authorized'])
    def test_word_limit_rejects_overlong_daily_analysis(self):
        p=copy.deepcopy(self.p)
        p['challenge']=' '.join(['Long']*130)
        self.assertEqual(self.go(p)['reason'],'word_budget_exceeded')
    def test_assessment_survives_without_fabricated_counterargument(self):
        p=copy.deepcopy(self.p)
        p['review_status']='assessment_survives'
        p['challenge']=''
        p['evidence_against']=[]
        r=self.go(p)
        self.assertEqual(r['review_status'],'assessment_survives')
        self.assertEqual(r['independent_operator_count'],1)
    def test_weekly_requires_explicit_comparison(self):
        p=copy.deepcopy(self.p)
        p['cadence']='weekly'
        r=self.go(p)
        self.assertEqual(r['reason'],'weekly_delta_missing')
        p['weekly_change']='The baseline changed based on added reports.'
        self.assertEqual(self.go(p)['review_status'],'supported_challenge')
    def test_stale_evidence_abstains(self):
        self.l._source_revisions[('src2','rev2')]['published_at']='2026-09-20T00:00:00+04:00'
        self.assertEqual(self.go()['reason'],'stale_evidence')
    def test_missing_or_inconsistent_schema_fails(self):
        p=copy.deepcopy(self.p)
        p['invented']=1
        self.assertEqual(self.go(p)['reason'],'invalid_review_schema')
        p=copy.deepcopy(self.p)
        p['target_event_id']='evt_unknown'
        self.assertEqual(self.go(p)['reason'],'unlinked_claim')
    def test_unhashable_status_is_withheld_not_runtime_crash(self):
        p=copy.deepcopy(self.p)
        p['review_status']=['supported_challenge']
        self.assertEqual(self.go(p)['reason'],'invalid_review_status')
    def test_unhashable_evidence_is_withheld_not_runtime_crash(self):
        p=copy.deepcopy(self.p)
        p['evidence_for']=[{'excerpt_id':'exc_1'}]
        self.assertEqual(self.go(p)['reason'],'unlinked_excerpt')
    def test_weekly_requires_three_distinct_events(self):
        p=copy.deepcopy(self.p)
        p['cadence']='weekly'
        p['weekly_change']='Changed from prior week.'
        r=build_report([p,p,p],ledger=self.l,as_of=NOW,
                       verified_families=self.fam,verified_languages=self.lang,
                       product='english',cadence='weekly',slot_id=SLOT)
        self.assertFalse(r['quality_gate_passed'])
        self.assertEqual(r['reason'],'weekly_needs_three_distinct_reviews')
    def test_missing_daily_review_is_visible_but_not_quality_green(self):
        r=build_report([],ledger=self.l,as_of=NOW,verified_families=self.fam,
                       verified_languages=self.lang,product='arabic',cadence='daily',slot_id=SLOT)
        self.assertEqual(r['sections'][0]['review_status'],'insufficient_evidence')
        self.assertFalse(r['quality_gate_passed'])
        self.assertEqual(r['reason'],'visible_degraded_notice_only')

    def test_daily_report_contains_one_visible_section(self):
        r=build_report([self.p],ledger=self.l,as_of=NOW,
                       verified_families=self.fam,verified_languages=self.lang,
                       product='english',cadence='daily',slot_id=SLOT)
        self.assertTrue(r['quality_gate_passed'])
        self.assertEqual(len(r['sections']),1)
        self.assertFalse(r['delivery_authorized'])

if __name__ == '__main__':
    unittest.main()
