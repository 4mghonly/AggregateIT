import unittest
from v2_naysayer_layout import render_review_html

class LayoutTests(unittest.TestCase):
    def base(self, product='english', cadence='daily'):
        return {'schema':'aggregateit-naysayer-report/1','product':product,'cadence':cadence,
                'slot_id':'2026-10-24T06:00:00+04:00','sections':[
                {'review_status':'supported_challenge', 'lead_assessment':'Synthetic escalation interpretation',
                 'challenge':'Alternative interpretation', 'critical_assumptions':['Timing'],
                 'what_would_change_the_assessment':['Verification'], 'weekly_change':'New info',
                 'cited_evidence':[{'excerpt_id':'exc_1','source_id':'src1','article_id':'a1','side':'for'}]}],
                'quality_gate_passed':True,'delivery_authorized':False}
    def test_english_daily_contains_critical_panel_and_reference(self):
        html=render_review_html(self.base());self.assertIn('Critical assessment',html)
        self.assertIn('exc_1',html);self.assertIn('lang="en"',html)
        self.assertIn('NOT FOR DELIVERY',html)
    def test_arabic_daily_is_rtl_and_has_named_panel(self):
        html=render_review_html(self.base('arabic'))
        self.assertIn('dir="rtl"',html);self.assertIn('اختبار الفرضية',html)
    def test_unavailable_has_honest_fallback_in_both_languages(self):
        for p,s in [('english','Insufficient evidence'),('arabic','الأدلة غير كافية')]:
            b=self.base(p);b['sections']=[{'review_status':'insufficient_evidence','cited_evidence':[]}];b['quality_gate_passed']=False
            self.assertIn(s,render_review_html(b))
    def test_unsafe_source_input_is_escaped(self):
        b=self.base();b['sections'][0]['challenge']='<script>alert(1)</script>'
        h=render_review_html(b)
        self.assertNotIn('<script>',h);self.assertIn('&lt;script&gt;',h)
    def test_weekly_requires_minimum_three_sections_and_no_delivery(self):
        b=self.base(cadence='weekly')
        with self.assertRaises(ValueError):render_review_html(b)
        b['sections']*=3
        h=render_review_html(b)
        self.assertIn('Weekly challenge review',h)
        self.assertIn('NOT FOR DELIVERY',h)
    def test_authorized_delivery_mark_is_refused_even_in_mock(self):
        b=self.base();b['delivery_authorized']=True
        with self.assertRaises(ValueError):render_review_html(b)

if __name__=='__main__':unittest.main()
