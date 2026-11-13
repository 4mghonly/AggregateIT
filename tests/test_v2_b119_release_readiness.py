"""B119: no parser parity or incomplete history can be promoted into release."""
import unittest
from datetime import date, timedelta
from v2_b119_release_readiness import assess, stable_candidate_sha

def fixtures():
    window=[(date(2026,11,5)-timedelta(days=6-i)).isoformat() for i in range(7)]
    paired={'schema':'aggregateit-v2-b115-seven-day-paired-history/1',
            'can_release':False,'window':window,
            'seven_positive_bilingual_days':True,
            'seven_distinct_paired_capture_dates':True,
            'daily':{day:{'capture_runs':1,'english_positive':True,'arabic_positive':True} for day in window}}
    live={'schema':'aggregateit-v2-b46-live-chain/1','can_release':False,
          'four_products':{'schema':'aggregateit-v2-b47-four-product-held/1','real_7_day_reporting_verified':False},
          'native':{'status':'HELD_VALID_NATIVE_PAGES','native_pages':[{}]*5}}
    shadow={'schema':'aggregateit-v2-b49-single-slot-preflight/1','can_release':False,
            'all_parser_parity':True,'all_source_headline_parity':True}
    pixel={'schema':'aggregateit-v2-b99-pixel-qa/1','can_release':False,
           'all_objective_checks_pass':True}
    history={'schema':'aggregateit-v2-b95-b97-history/1','can_release':False,
             'seven_day_evidence_met':False}
    conflicts={'schema':'aggregateit-v2-b112-history-conflicts/1','can_release':False,
               'conflicting_days':1}
    return live,paired,shadow,pixel,history,conflicts

class B119AuditTests(unittest.TestCase):
    def test_valid_b115_and_objective_pngs_do_not_prove_models_or_delivery(self):
        a=assess(*fixtures())
        self.assertTrue(a['gates']['b115_seven_genuine_bilingual_dates'])
        self.assertTrue(a['gates']['v2_five_native_pages'])
        self.assertFalse(a['gates']['v1_full_editorial_and_model_parity'])
        self.assertFalse(a['gates']['v1_v2_same_slot_visual_equivalence'])
        self.assertFalse(a['gates']['v1_v2_authenticated_delivery_and_rollback_parity'])
        self.assertEqual(a['release_status'],'HOLD')
        self.assertFalse(a['can_release'])

    def test_b125_evidence_requires_exact_sha_and_verified_dates(self):
        evidence={'schema':'aggregateit-v2-b125-independent-reconciliation/1',
                  'candidate_sha':'b67a9e4115f4f88049716d608e54a6d06ef5f15f',
                  'seven_verified':True,'verified_dates':fixtures()[1]['window'],
                  'can_release':False}
        accepted=assess(*fixtures(),candidate_sha=evidence['candidate_sha'],b125=evidence)
        self.assertTrue(accepted['gates']['b125_authenticated_same_capture_seven_dates'])
        evidence['candidate_sha']='c'*40
        rejected=assess(*fixtures(),candidate_sha='b67a9e4115f4f88049716d608e54a6d06ef5f15f',b125=evidence)
        self.assertFalse(rejected['gates']['b125_authenticated_same_capture_seven_dates'])
        self.assertFalse(rejected['can_release'])

    def test_b126_weekly_roster_does_not_promote_full_product(self):
        from datetime import date,timedelta
        days=[(date(2026,11,6)+timedelta(days=i)).isoformat() for i in range(7)]
        evidence={'schema':'aggregateit-v2-b126-weekly-editorial-audit/1',
                  'candidate_sha':'b67a9e4115f4f88049716d608e54a6d06ef5f15f',
                  'source_roster_seven_days':True,'verified_dates':days,
                  'full_model_parity':False,'weekly_full_product_verified':False,
                  'can_release':False,'issues':[]}
        inputs=list(fixtures())
        inputs[1]['window']=days
        inputs[1]['daily']={day:{'capture_runs':1,'english_positive':True,'arabic_positive':True} for day in days}
        out=assess(*inputs,candidate_sha=evidence['candidate_sha'],b126=evidence)
        self.assertTrue(out['gates']['b126_attributed_weekly_bilingual_source_roster'])
        self.assertFalse(out['gates']['v2_weekly_both_languages_seven_real_days'])
        self.assertFalse(out['gates']['v1_full_editorial_and_model_parity'])
        self.assertFalse(out['can_release'])

    def test_b127_queue_reconciled_but_not_adjudicated(self):
        inputs=list(fixtures())
        days=inputs[1]['window']
        evidence={'schema':'aggregateit-v2-b127-identity-matched-review/1',
                  'candidate_sha':'b67a9e4115f4f88049716d608e54a6d06ef5f15f',
                  'evidence_reconciled':True,'disagreement_count':73,
                  'review_status':'PENDING_INDEPENDENT_REVIEW',
                  'independent_adjudication_verified':False,
                  'publisher_rights_verified':False,
                  'can_release':False,'issues':[]}
        result=assess(*inputs,candidate_sha=evidence['candidate_sha'],b127=evidence)
        self.assertTrue(result['gates']['b127_identity_matched_disagreements'])
        self.assertFalse(result['gates']['editorial_disagreements_independently_adjudicated'])
        self.assertFalse(result['can_release'])

    def test_b128_triage_does_not_claim_adjudication(self):
        inputs=list(fixtures())
        evidence={'schema':'aggregateit-v2-b128-adjudication-readiness/1',
                  'candidate_sha':'b67a9e4115f4f88049716d608e54a6d06ef5f15f',
                  'review_queue_valid':True,'disagreement_count':73,'pending_count':73,
                  'reviewed_count':0,'independent_adjudication_verified':False,
                  'weekly_full_product_verified':False,'can_release':False,'issues':[]}
        result=assess(*inputs,candidate_sha=evidence['candidate_sha'],b128=evidence)
        self.assertTrue(result['gates']['b128_review_workload_classified'])
        self.assertFalse(result['gates']['editorial_disagreements_independently_adjudicated'])
        self.assertFalse(result['gates']['v2_weekly_both_languages_seven_real_days'])
        self.assertFalse(result['can_release'])

    def test_b128_hybrid_evidence_gap_is_visible(self):
        inputs=list(fixtures())
        hybrid={'schema':'aggregateit-v2-b128-hybrid-closure/1',
                'candidate_sha':'b67a9e4115f4f88049716d608e54a6d06ef5f15f',
                'adjudication':{'total':73,'accepted':0,'pending':73,'independent_adjudication_verified':False},
                'weekly':{'verified':False,'missing_snapshot_days':{'english':6,'arabic':6}},
                'release_status':'HOLD','can_release':False,'issues':[]}
        result=assess(*inputs,candidate_sha=hybrid['candidate_sha'],b128_hybrid=hybrid)
        self.assertTrue(result['gates']['b128_hybrid_gap_evidence_reconciled'])
        self.assertFalse(result['gates']['editorial_disagreements_independently_adjudicated'])
        self.assertFalse(result['gates']['v2_weekly_both_languages_seven_real_days'])

    def test_missing_or_conflicting_evidence_fails_closed(self):
        a=assess({},{},{},{},{},{})
        self.assertFalse(any(a['gates'].values()))
        self.assertEqual(a['release_status'],'HOLD')
        inputs=list(fixtures());inputs[1]['daily'][inputs[1]['window'][2]]['arabic_positive']=False
        self.assertFalse(assess(*inputs)['gates']['b115_seven_genuine_bilingual_dates'])

    def test_fixed_commit_not_inferred_from_aggregate_dates(self):
        self.assertIsNone(stable_candidate_sha('/does/not/exist', fixtures()[1]['window'],
                                               today=date(2026,11,5)))
        a=assess(*fixtures())
        self.assertFalse(a['gates']['stable_candidate_seven_genuine_dates'])

if __name__=='__main__':
    unittest.main()
