"""Synthetic bilingual daily publication compiler tests."""
import unittest
from v2_product_compiler import compile_daily
SLOT='2026-10-24T06:00:00+04:00'
def plan(product):
    lang='en' if product=='english' else 'ar'
    return {'schema':'aggregateit-editorial-plan/1','delivery_authorized':False,'slot_id':SLOT,'product':product,'language':lang,
        'items':[{'event_id':'evt_1','region':'gcc','topic':'geopolitics' if product=='english' else 'diplomacy',
                  'reporting_status':'publisher_attributed_not_independently_verified','change':'new',
                  'evidence':{'excerpt_id':'ex_1','source_id':'s1','quote':'Synthetic test observation',
                              'source_url':'https://example.org/article','original_language':lang}}],
        'missing_target_regions':['somalia']}
class CompilerTests(unittest.TestCase):
    def test_eng_does_not_manufacture_market_data(self):
        r=compile_daily(editorial_plan=plan('english'))
        self.assertEqual(r['market_data_status'],'unavailable')
        self.assertEqual(r['stories'][0]['assessment'],None)
        self.assertFalse(r['delivery_authorized'])
    def test_ar_only_geopolitics_and_coverage_gaps(self):
        r=compile_daily(editorial_plan=plan('arabic'))
        self.assertEqual(r['market_data_status'],'not_applicable')
        self.assertEqual(r['coverage_gaps'],['somalia'])
    def test_arabic_market_topic_is_rejected(self):
        p=plan('arabic');p['items'][0]['topic']='markets'
        with self.assertRaises(ValueError):compile_daily(editorial_plan=p)
    def test_arabic_market_snapshot_rejected(self):
        with self.assertRaises(ValueError):compile_daily(editorial_plan=plan('arabic'),market_observations=[{'x':1}])
    def test_claim_without_source_excerpt_is_rejected(self):
        p=plan('english');p['items'][0]['evidence']['excerpt_id']=''
        with self.assertRaises(ValueError):compile_daily(editorial_plan=p)
    def test_wrong_translation_unverified_is_rejected(self):
        p=plan('arabic');p['items'][0]['evidence']['original_language']='fa'
        with self.assertRaises(ValueError):compile_daily(editorial_plan=p)
    def test_critic_cross_product_rejected(self):
        c={'schema':'aggregateit-naysayer-report/1','delivery_authorized':False,'product':'arabic','cadence':'daily','slot_id':SLOT,'sections':[{'review_status':'withheld'}]}
        with self.assertRaises(ValueError):compile_daily(editorial_plan=plan('english'),critic_report=c)
    def test_critic_degraded_is_visible(self):
        c={'schema':'aggregateit-naysayer-report/1','delivery_authorized':False,'product':'english','cadence':'daily','slot_id':SLOT,'sections':[{'review_status':'insufficient_evidence'}]}
        r=compile_daily(editorial_plan=plan('english'),critic_report=c)
        self.assertEqual(r['naysayer_status'],'insufficient_evidence')
    def test_nan_market_value_is_rejected(self):
        with self.assertRaises(ValueError):
            compile_daily(editorial_plan=plan('english'),market_observations=[{'symbol':'WTI','source':'eia','observed_at':SLOT,'value':float('nan'),'unit':'USD'}])
    def test_market_observation_with_real_provenance_is_preserved(self):
        row={'symbol':'WTI','source':'eia','observed_at':SLOT,'value':82.1,'unit':'USD'}
        r=compile_daily(editorial_plan=plan('english'),market_observations=[row])
        self.assertEqual(r['market_data_status'],'observed_unverified')
        self.assertEqual(r['market_observations'][0]['source'],'eia')
    def test_verified_claim_is_not_inferred_from_schema(self):
        p=plan('english');p['items'][0]['reporting_status']='independently_verified'
        with self.assertRaises(ValueError):compile_daily(editorial_plan=p)
if __name__=='__main__':unittest.main()
