"""A8: a single bounded article-fetch => B3/B4 => 4K no-post transaction."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from v2_a8_single_run import run_no_post_chain

EN = b'''<html><body><article><p>Seven people have been killed in an attack on a funeral in central Jordan, officials said.</p><p>At least 34 others were injured at the church in Jordan, the report added.</p></article></body></html>'''
AR = '''<html lang="ar"><body><div class="wysiwyg wysiwyg--all-content"><p>ارتفعت حصيلة قتلى الهجوم في كنيسة بمحافظة الكرك في الأردن بحسب السلطات المحلية.</p><p>وقال مسؤولون أردنيون إن التحقيقات بشأن الهجوم ما تزال جارية.</p></div></body></html>'''.encode('utf8')
SOURCES=[
 {'source_id':'en-001','language':'en','url':'https://www.bbc.co.uk/news/articles/demo','headline':'Seven killed at funeral attack in Jordan','published_at':'2026-10-23T19:46:30+00:00'},
 {'source_id':'ar-s003','language':'ar','url':'https://www.aljazeera.net/news/2026/10/24/demo','headline':'ارتفاع قتلى هجوم الكنيسة في الأردن','published_at':'2026-10-24T07:49:59+03:00'},
]
NOW='2026-10-24T12:30:00+04:00'
SLOT='2026-10-24T12:00:00+04:00'

def fixture_fetch(url,*,timeout):
    assert timeout<=12
    payload=EN if 'bbc' in url else AR
    return {'status':200,'content_type':'text/html; charset=utf-8','final_url':url,'body':payload}


def fake_render(english,arabic,*,slot_id,output_dir):
    assert english['items'] and arabic['items']
    target=Path(output_dir)
    target.mkdir(parents=True)
    pages=[]
    for product,page in [('english',1),('english',2),('arabic',1),('arabic',2),('arabic',3)]:
        raw=b'\x89PNG\r\n\x1a\n' + product.encode('utf8')+str(page).encode('ascii')
        p=target/(product+f'-no-post-{page}.png')
        p.write_bytes(raw)
        from hashlib import sha256
        pages.append({'product':product,'page':page,'path':p.name,'sha256':sha256(raw).hexdigest()})
    return {'pages':pages,'discord_sent':False,'llm_called':False,'delivery_authorized':False}


class SingleRunTests(unittest.TestCase):
    def test_network_is_off_by_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError,'network_explicitly_disabled'):
                run_no_post_chain(SOURCES,as_of=NOW,slot_id=SLOT,output_dir=Path(tmp)/'edition')

    def test_single_process_uses_real_body_and_grounded_country(self):
        with tempfile.TemporaryDirectory() as tmp, patch('v2_a8_single_run.render_held_editions',side_effect=fake_render):
            out=Path(tmp)/'edition'
            result=run_no_post_chain(SOURCES,as_of=NOW,slot_id=SLOT,output_dir=out,fetcher=fixture_fetch)
            self.assertEqual(len(result['documents']),2)
            self.assertEqual(result['ledger']['excerpts'],2)
            self.assertEqual(result['products']['english']['selected'],1)
            self.assertEqual(result['products']['arabic']['selected'],1)
            self.assertEqual(result['documents'][0]['region'],'jordan')
            self.assertEqual(result['documents'][1]['region'],'jordan')
            self.assertTrue(all(r['excerpt_integrity_verified'] for r in result['documents']))
            self.assertFalse(result['web_source_independence_verified'])
            self.assertFalse(result['model_called'])
            self.assertFalse(result['discord_sent'])
            self.assertFalse(result['delivery_authorized'])
            self.assertEqual(len(result['pages']),5)
            self.assertEqual(len(list(out.glob('*.png'))),5)
            self.assertEqual(json.loads((out/'manifest.json').read_text())['schema'],result['schema'])
            self.assertFalse(result['live_http_performed'])
            self.assertEqual(result['source_transport'],'injected_test_bytes')

    def test_failed_second_fetch_leaves_no_output_directory(self):
        calls=0
        def bad_fetch(url,*,timeout):
            nonlocal calls
            calls+=1
            if calls==2:raise TimeoutError('source_timeout')
            return fixture_fetch(url,timeout=timeout)
        with tempfile.TemporaryDirectory() as tmp, patch('v2_a8_single_run.render_held_editions',side_effect=fake_render):
            out=Path(tmp)/'edition'
            with self.assertRaises(TimeoutError):
                run_no_post_chain(SOURCES,as_of=NOW,slot_id=SLOT,output_dir=out,fetcher=bad_fetch)
            self.assertFalse(out.exists())

    def test_bad_source_host_rejected_before_fetch(self):
        calls=[]
        altered=[dict(SOURCES[0],url='https://127.1/news'), SOURCES[1]]
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                run_no_post_chain(altered,as_of=NOW,slot_id=SLOT,output_dir=Path(tmp)/'edition',fetcher=lambda *args,**kw:calls.append(True))
            self.assertEqual(calls,[])

    def test_unrelated_source_domain_not_admitted(self):
        altered=[dict(SOURCES[0],url='https://bbc.co.uk.evil.example/news'), SOURCES[1]]
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                run_no_post_chain(altered,as_of=NOW,slot_id=SLOT,output_dir=Path(tmp)/'edition',fetcher=fixture_fetch)

    def test_redirect_to_other_host_rejected(self):
        def evil_fetch(url,*,timeout):
            packet=fixture_fetch(url,timeout=timeout)
            return dict(packet,final_url='https://internal.example.invalid/news')
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError,'redirected_article_host'):
                run_no_post_chain(SOURCES,as_of=NOW,slot_id=SLOT,output_dir=Path(tmp)/'edition',fetcher=evil_fetch)

    def test_duplicate_language_not_misreported_as_bilingual(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                run_no_post_chain([SOURCES[0],SOURCES[0]],as_of=NOW,slot_id=SLOT,output_dir=Path(tmp)/'edition',fetcher=fixture_fetch)

    def test_render_failure_does_not_leave_half_edition(self):
        def broken_render(*args,**kwargs):
            d=Path(kwargs['output_dir']);d.mkdir(parents=True)
            (d/'english-no-post-1.png').write_bytes(b'half-edition')
            raise RuntimeError('arabic_render_failed')
        with tempfile.TemporaryDirectory() as tmp,patch('v2_a8_single_run.render_held_editions',side_effect=broken_render):
            out=Path(tmp)/'edition'
            with self.assertRaises(RuntimeError):
                run_no_post_chain(SOURCES,as_of=NOW,slot_id=SLOT,output_dir=out,fetcher=fixture_fetch)
            self.assertFalse(out.exists())

    def test_actual_native_five_pages_in_one_operation(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/'edition'
            result=run_no_post_chain(SOURCES,as_of=NOW,slot_id=SLOT,output_dir=out,fetcher=fixture_fetch)
            self.assertEqual(len(result['pages']),5)
            for row in result['pages']:
                with Image.open(out/row['path']) as image:
                    self.assertEqual(image.size,(3840,2160))
            self.assertFalse(result['delivery_authorized'])

if __name__=='__main__': unittest.main()
