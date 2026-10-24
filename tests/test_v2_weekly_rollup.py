"""Weekly editorial source/market provenance regression tests."""
import unittest
from v2_weekly_rollup import rollup_week
END='2026-10-24T06:00:00+04:00'

def plan(product,day,version='v1',change='unknown_no_baseline',region='gcc',name='evt1'):
    return {'schema':'aggregateit-editorial-plan/1','product':product,'delivery_authorized':False,
            'as_of':f'2026-10-{day:02d}T06:00:00+04:00',
            'items':[{'event_id':name,'version_id':version,'region':region,'priority':70,'change':change,
                      'evidence':{'source_id':'s1','excerpt_id':'ex1','source_url':'https://example.org/story',
                                  'quote':'Synthetic source text','original_language':'en' if product=='english' else 'ar'}}]}

class WeeklyRollupTests(unittest.TestCase):
    def test_dedup_event_and_detect_real_version_change(self):
        r=rollup_week([plan('english',20),plan('english',21),plan('english',23,'v2')],product='english',as_of=END)
        self.assertEqual(r['unique_events'],1)
        self.assertEqual(r['stories'][0]['revision_count'],2)
        self.assertEqual(r['stories'][0]['change_status'],'updated_during_week')
        self.assertFalse(r['delivery_authorized'])
    def test_no_baseline_does_not_claim_new_event(self):
        r=rollup_week([plan('arabic',23)],product='arabic',as_of=END)
        self.assertEqual(r['stories'][0]['change_status'],'observed_no_verified_baseline')
    def test_regional_coverage_gaps_are_explicit(self):
        r=rollup_week([plan('arabic',21),plan('arabic',22,region='yemen',name='evt2')],product='arabic',as_of=END)
        self.assertEqual(r['unique_events'],2)
        self.assertIn('somalia',r['regions_uncovered'])
    def test_arabic_rejects_financial_data(self):
        with self.assertRaisesRegex(ValueError,'arabic_market_not_supported'):
            rollup_week([plan('arabic',23)],product='arabic',as_of=END,market_snapshots=[{'x':1}])
    def test_measured_market_change_needs_two_dated_readings(self):
        obs=[{'instrument':'WTI','source':'eia','observed_at':'2026-10-20T04:00:00+04:00','value':90,'unit':'USD/bbl'},
             {'instrument':'WTI','source':'eia','observed_at':'2026-10-23T04:00:00+04:00','value':99,'unit':'USD/bbl'}]
        r=rollup_week([plan('english',23)],product='english',as_of=END,market_snapshots=obs)
        self.assertAlmostEqual(r['market_changes'][0]['change_pct'],10)
    def test_tradingview_widget_cannot_supply_backend_prices(self):
        with self.assertRaises(ValueError):
            rollup_week([plan('english',23)],product='english',as_of=END,market_snapshots=[
                {'instrument':'X','source':'tradingview_widget','observed_at':END,'value':1,'unit':'index'}])
    def test_one_market_observation_is_unknown_delta(self):
        r=rollup_week([plan('english',23)],product='english',as_of=END,market_snapshots=[
            {'instrument':'X','source':'eia','observed_at':END,'value':1,'unit':'index'}])
        self.assertIsNone(r['market_changes'][0]['change_pct'])
    def test_stale_or_wrong_product_is_refused(self):
        with self.assertRaises(ValueError):rollup_week([plan('english',15)],product='english',as_of=END)
        with self.assertRaises(ValueError):rollup_week([plan('arabic',23)],product='english',as_of=END)
    def test_retains_original_source_quote_with_evidence_identity(self):
        r=rollup_week([plan('english',23)],product='english',as_of=END)
        self.assertEqual(r['stories'][0]['evidence']['quote'],'Synthetic source text')
        self.assertEqual(r['stories'][0]['evidence']['excerpt_id'],'ex1')
    def test_missing_excerpt_id_is_refused(self):
        p=plan('english',23);p['items'][0]['evidence']['excerpt_id']=''
        with self.assertRaises(ValueError):rollup_week([p],product='english',as_of=END)

if __name__=='__main__':unittest.main()
