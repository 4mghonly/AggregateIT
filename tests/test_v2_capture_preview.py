"""Evidence-only bilingual preview must not suggest full collection or verification."""
import json
import unittest
from pathlib import Path
from v2_external_capture import compile_web_captures
from v2_capture_preview import render_capture_preview

ROOT=Path(__file__).resolve().parents[1]

class CapturePreviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        f=json.loads((ROOT/'fixtures/v2/public_web_excerpt_rehearsal_2026-10-24.json').read_text(encoding='utf8'))
        reg=json.loads((ROOT/'config/v2/source_registry.json').read_text(encoding='utf8'))
        cls.report=compile_web_captures(f['captures'],registry=reg,observed_at=f['observed_at'],slot_id=f['slot_id'])

    def test_english_preview_cites_source_and_is_unverified(self):
        html=render_capture_preview(self.report,product='english')
        self.assertIn('lang="en"',html)
        self.assertIn('Source excerpts',html)
        self.assertIn('en-107',html)
        self.assertIn('exc_',html)
        self.assertIn('UNVERIFIED',html)
        self.assertNotIn('2026-10-23T12:00:00',html)
        self.assertNotIn('UAE MARKETS ROSE',html)

    def test_arabic_preview_preserves_original_quotes_and_is_rtl(self):
        html=render_capture_preview(self.report,product='arabic')
        self.assertIn('lang="ar" dir="rtl"',html)
        self.assertIn('ar-s116',html)
        self.assertIn('ar-s011',html)
        self.assertIn('ar-s003',html)
        self.assertIn('اليمن',html)
        self.assertIn('المقتطفات',html)
        self.assertNotIn('Market performance',html)
        self.assertIn('لم يتم تشغيل',html)
        self.assertNotIn('No live feed collector',html)

    def test_html_escapes_quote_and_refuses_javascript_link(self):
        import copy
        r=copy.deepcopy(self.report)
        r['products']['english']['stories'][0]['quote']='<script>alert(1)</script>'
        html=render_capture_preview(r,product='english')
        self.assertNotIn('<script>alert(1)</script>',html)
        self.assertIn('&lt;script&gt;',html)
        r['products']['english']['stories'][0]['source_url']='javascript:alert(1)'
        with self.assertRaises(ValueError):render_capture_preview(r,product='english')

    def test_denies_claimed_publishing(self):
        import copy
        r=copy.deepcopy(self.report)
        r['delivery_authorized']=True
        with self.assertRaises(ValueError):render_capture_preview(r,product='english')

if __name__=='__main__':unittest.main()
