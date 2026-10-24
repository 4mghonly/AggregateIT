"""Bilingual weekly renderer compatibility and factual-withholding regressions."""
import unittest
from v2_weekly_layout import render_weekly_html


class WeeklyPublicationTests(unittest.TestCase):
    def report(self, product='english'):
        return {
            'schema':'aggregateit-v2-weekly-rollup/1','product':product,
            'as_of':'2026-10-24T06:00:00+04:00','window_days':7,
            'days_with_snapshots':4,'unique_events':2,
            'stories':[
                {'event_id':'evt_<script>alert(1)</script>','region':'gcc',
                 'priority':82,'change_status':'updated_during_week',
                 'revision_count':2,'observation_days':4,
                 'evidence':{'source_id':'source-01','excerpt_id':'exc-23',
                             'source_url':'https://example.org/news/2',
                             'original_language':'en' if product=='english' else 'ar'},
                 'reporting_status':'publisher_attributed_not_independently_verified'}
            ],
            'omitted_over_budget':0,'regions_covered':['gcc'],
            'regions_uncovered':['somalia'] if product=='arabic' else [],
            'market_changes':[{'instrument':'WTI','source':'eia','unit':'USD/bbl',
                               'first_at':'2026-10-19T12:00:00+04:00',
                               'last_at':'2026-10-23T12:00:00+04:00',
                               'first_value':90,'last_value':99,'change_pct':10}] if product=='english' else [],
            'analysis_status':'requires_independent_source_and_editorial_verification',
            'naysayer_status':'not_supplied','delivery_authorized':False,
        }

    def test_english_weekly_is_evidence_linked_and_has_measured_market_panel(self):
        h=render_weekly_html(self.report())
        self.assertIn('lang="en" dir="ltr"',h)
        self.assertIn('USD/bbl',h)
        self.assertIn('+10.000%',h)
        self.assertIn('https://example.org/news/2',h)
        self.assertIn('SYNTHETIC / UNVERIFIED',h)
        self.assertNotIn('<script>alert(1)</script>',h)

    def test_arabic_weekly_is_rtl_and_explicitly_nonfinancial(self):
        h=render_weekly_html(self.report('arabic'))
        self.assertIn('lang="ar" dir="rtl"',h)
        self.assertIn('الصومال',h)
        self.assertNotIn('Market performance',h)
        self.assertNotIn('WTI',h)

    def test_weekly_declines_naysayer_unless_grounded(self):
        h=render_weekly_html(self.report())
        self.assertIn('Evidence insufficient for a critical review',h)

    def test_rejects_arabic_market_leakage(self):
        r=self.report('arabic')
        r['market_changes']=[{'instrument':'WTI'}]
        with self.assertRaises(ValueError):render_weekly_html(r)

    def test_rejects_unverified_link_schemes(self):
        r=self.report()
        r['stories'][0]['evidence']['source_url']='javascript:alert(1)'
        with self.assertRaises(ValueError):render_weekly_html(r)

    def test_refuses_claimed_live_publication(self):
        r=self.report()
        r['delivery_authorized']=True
        with self.assertRaises(ValueError):render_weekly_html(r)

    def test_refuses_lost_weekly_source_records(self):
        r=self.report()
        r['stories'][0]['evidence']['excerpt_id']=''
        with self.assertRaises(ValueError):render_weekly_html(r)


if __name__=='__main__':
    unittest.main()
