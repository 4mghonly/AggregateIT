"""B47 actual weekly source-bound PDF rendering and incomplete history guards."""
import unittest
from io import BytesIO
from pypdf import PdfReader
from v2_b47_weekly_pdf_preview import generate_held_weekly_pdf

def report(product):
    return {'schema':'aggregateit-v2-weekly-rollup/1','product':product,
            'delivery_authorized':False,'window_days':7,'days_with_snapshots':1,
            'stories':[{'region':'somalia','evidence':{'source_id':'en-001' if product=='english' else 'ar-s003',
            'excerpt_id':'exc-demo','quote':('Somalia officials issued an update.' if product=='english'
              else 'أصدر مسؤولون في الصومال بياناً بشأن التطورات.'),
            'source_url':'https://www.example.org/news/1'}}]}
class WeeklyPdfTests(unittest.TestCase):
    def test_english_partial_source_pdf_is_valid_but_unsendable(self):
        r=generate_held_weekly_pdf(report('english'))
        self.assertTrue(r['bytes'].startswith(b'%PDF-'))
        self.assertFalse(r['complete_week'])
        self.assertEqual(len(PdfReader(BytesIO(r['bytes'])).pages),r['pages'])
        self.assertFalse(r['can_send'])
    def test_arabic_pdf_has_usable_font_and_page(self):
        r=generate_held_weekly_pdf(report('arabic'))
        self.assertGreater(len(r['bytes']),2000)
        self.assertEqual(r['source_bound_story_count'],1)
        self.assertFalse(r['rights_verified'])
    def test_no_fake_full_week_claim(self):
        r=report('english');r['days_with_snapshots']=8
        with self.assertRaisesRegex(ValueError,'invalid_weekly_observed_days'):
            generate_held_weekly_pdf(r)
    def test_insecure_source_url_refused(self):
        r=report('arabic');r['stories'][0]['evidence']['source_url']='http://example.org'
        with self.assertRaisesRegex(ValueError,'untrusted_weekly_source_url'):
            generate_held_weekly_pdf(r)
    def test_delivery_authority_refused(self):
        r=report('english');r['delivery_authorized']=True
        with self.assertRaises(ValueError):
            generate_held_weekly_pdf(r)
if __name__=='__main__':unittest.main()
