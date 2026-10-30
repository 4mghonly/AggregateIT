"""B47 four-product genuine-excerpt integration: bounded, non-sendable."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from PIL import Image
from hashlib import sha256
from v2_b46_live_editorial import compile_captured_articles
from v2_b47_four_product_held import compose_held_products

AS_OF='2026-10-27T08:00:00+00:00'
SLOT='2026-10-27T12:00:00+04:00'
EN=('Officials in Somalia said that security representatives met to discuss '
    'security developments and publicly available statements about the situation.')
AR='أكد مسؤولون في الصومال عقد مباحثات دبلوماسية مع ممثلين إقليميين لبحث التطورات السياسية ومناقشة بيانات الاجتماع المتعلق بالعلاقات الإقليمية.'

def capture_bilingual():
    e={'product':'english','source_id':'en-001',
       'article_url':'https://www.bbc.com/news/articles/c123-b47',
       'title':'Somalia security representatives hold discussions',
       'published_at':'2026-10-27T07:00:00+00:00',
       'html_bytes':('<article><p>'+EN+'</p><p>'+EN+'</p></article>').encode()}
    a={'product':'arabic','source_id':'ar-s003',
       'article_url':'https://www.aljazeera.net/news/2026/10/27/b47',
       'title':'مباحثات دبلوماسية في الصومال بشأن العلاقات الإقليمية',
       'published_at':'2026-10-27T07:00:00+00:00',
       'html_bytes':('<div class="wysiwyg--all-content"><p>'+AR+'</p><p>'+AR+'</p></div>').encode()}
    return compile_captured_articles([e,a],as_of=AS_OF,slot_id=SLOT)

def fixture_render(editorial,*,output_dir,pulse_snapshot=None,macro_snapshot=None):
    output_dir.mkdir()
    pages=[]
    for product,number in [('english',2),('arabic',3)]:
        for n in range(1,number+1):
            fn=output_dir/f'{product}-no-post-{n}.png'
            Image.new('RGB',(3840,2160)).save(fn,format='PNG')
            pages.append({'product':product,'page':n,'sha256':sha256(fn.read_bytes()).hexdigest()})
    return {'status':'HELD_VALID_NATIVE_PAGES','native_pages':pages}

class B47HeldTests(unittest.TestCase):
    def test_four_products_two_packets_and_incomplete_week(self):
        with tempfile.TemporaryDirectory() as td,patch('v2_b47_four_product_held.render_genuine_held',side_effect=fixture_render):
            record=compose_held_products(capture_bilingual(),output_dir=Path(td)/'native',as_of=AS_OF)
        self.assertEqual(set(record['daily']),{'english','arabic'})
        self.assertEqual(set(record['weekly']),{'english','arabic'})
        self.assertEqual(record['daily']['english']['page_count'],2)
        self.assertEqual(record['daily']['arabic']['page_count'],3)
        self.assertEqual(record['daily']['english']['destination_key'],'discord_webhook')
        self.assertEqual(record['daily']['arabic']['destination_key'],'discord_webhook_arabic')
        self.assertEqual(record['weekly']['english']['days_with_real_daily_snapshots'],1)
        self.assertFalse(record['real_7_day_reporting_verified'])
        self.assertTrue(record['weekly_pdf_produced'])
        self.assertTrue(record['weekly']['arabic']['discord_packet_prepared'])
        self.assertFalse(record['weekly']['arabic']['complete_seven_day_history'])
        self.assertFalse(record['can_release'])
    def test_missing_arabic_cannot_be_faked_by_weekly_fixtures(self):
        editorial=capture_bilingual();editorial['products']['arabic']['story_count']=0
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(ValueError,'cannot_substitute_synthetic'):
                compose_held_products(editorial,output_dir=Path(td)/'native',as_of=AS_OF)
    def test_invalid_native_bytes_fail_checksum(self):
        def wrong(e,*,output_dir,pulse_snapshot=None,macro_snapshot=None):
            m=fixture_render(e,output_dir=output_dir)
            m['native_pages'][0]['sha256']='0'*64
            return m
        with tempfile.TemporaryDirectory() as td,patch('v2_b47_four_product_held.render_genuine_held',side_effect=wrong):
            with self.assertRaisesRegex(ValueError,'disk_png_hash_mismatch'):
                compose_held_products(capture_bilingual(),output_dir=Path(td)/'native',as_of=AS_OF)
    def test_wrong_authority_or_timezone_rejected(self):
        e=capture_bilingual();e['can_send']=True
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(ValueError):
                compose_held_products(e,output_dir=Path(td),as_of=AS_OF)
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(ValueError,'invalid_product_window'):
                compose_held_products(capture_bilingual(),output_dir=Path(td),as_of='2026-10-27T08:00:00')
    def test_genuine_source_quote_not_exported_in_metadata(self):
        with tempfile.TemporaryDirectory() as td,patch('v2_b47_four_product_held.render_genuine_held',side_effect=fixture_render):
            receipt=compose_held_products(capture_bilingual(),output_dir=Path(td)/'native',as_of=AS_OF)
        self.assertNotIn('Officials in Somalia',repr(receipt))
        self.assertNotIn('أكد مسؤولون',repr(receipt))
        self.assertFalse(receipt['discord_sent'])
if __name__=='__main__':unittest.main()
