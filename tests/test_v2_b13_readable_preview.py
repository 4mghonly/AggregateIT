"""B13 4K balanced bilingual design: five real pages, no unauthorized excerpts."""
from pathlib import Path
from tempfile import TemporaryDirectory
from PIL import Image
import unittest

from v2_b13_readable_preview import render_balanced_preview

REGIONS=['gcc','iran','iraq','yemen','sudan','sahel','north_africa','egypt','afghanistan','levant','somalia','jordan']

def plan(product):
    lang='ar' if product=='arabic' else 'en'
    tiles=[{'event_id':f'evt_{product}_{i}','region':r,'source_id':f'TEST{i}',
            'source_url':'https://example.org/test','subject_country':'AE' if i==0 else 'JO',
            'original_language':lang,'priority':95-i,
            'display_headline':('خبر افتراضي للتجربة حول تطورات المنطقة والتنسيق الأمني' if lang=='ar'
                                else 'Synthetic regional safety and emergency response exercise'),
            'synthetic':True,'rights_status':'synthetic_only',
            'publisher_facts_verified':False}
           for i,r in enumerate(REGIONS[:10])]
    return {'schema':'aggregateit-v2-b13-balanced-held-preview/1',
            'product':product,'language':lang,'tiles':tiles,
            'delivery_authorized':False,'rights_cleared':False}

class ReadablePreviewTests(unittest.TestCase):
    def test_all_five_4k_pages_come_from_actual_renderer(self):
        with TemporaryDirectory() as tmp:
            r=render_balanced_preview(plan('english'),plan('arabic'),output_dir=Path(tmp)/'pages')
            self.assertEqual(len(r['pages']),5)
            self.assertFalse(r['delivery_authorized'])
            self.assertFalse(r['discord_sent'])
            for record in r['pages']:
                self.assertEqual(len(record['sha256']),64)
                with Image.open(Path(tmp)/'pages'/record['filename']) as im:
                    self.assertEqual(im.size,(3840,2160))
    def test_real_publisher_headline_cannot_bypass_permission_hold(self):
        bad=plan('arabic')
        bad['tiles'][0].update(synthetic=False,rights_status='rights_hold',
                                display_headline='محتوى صحفي منسوخ بلا تصريح')
        with TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                render_balanced_preview(plan('english'),bad,output_dir=Path(tmp)/'pages')
            self.assertFalse((Path(tmp)/'pages').exists())
    def test_same_event_twice_rejected(self):
        bad=plan('english')
        bad['tiles'][1]['event_id']=bad['tiles'][0]['event_id']
        with TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                render_balanced_preview(bad,plan('arabic'),output_dir=Path(tmp)/'pages')
    def test_existing_directory_never_overwritten(self):
        with TemporaryDirectory() as tmp:
            dest=Path(tmp)/'pages';dest.mkdir();(dest/'keep').write_text('keep')
            with self.assertRaises(ValueError):
                render_balanced_preview(plan('english'),plan('arabic'),output_dir=dest)
            self.assertEqual((dest/'keep').read_text(),'keep')

if __name__=='__main__':unittest.main()
