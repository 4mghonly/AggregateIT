"""Native no-post renderer directly consumes evidence-gated B4 plans."""
import json,unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from v2_native_evidence_render import render_held_editions
from v2_arabic_application_rehearsal import arabic_synthetic_fixture
from v2_offline_rehearsal import run_offline_rehearsal
ROOT=Path(__file__).resolve().parents[1]

class NoPostEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        registry=json.loads((ROOT/'config/v2/source_registry.json').read_text(encoding='utf8'))
        run=run_offline_rehearsal(arabic_synthetic_fixture(),registry)
        cls.en=run['products']['english']['plan'];cls.ar=run['products']['arabic']['plan']
        cls.slot=cls.en['slot_id']
    def test_untrusted_deliverability_refused_before_image_work(self):
        en={**self.en,'delivery_authorized':True}
        with TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError,'untrusted_edition_plan'):
                render_held_editions(en,self.ar,slot_id=self.slot,output_dir=Path(tmp))
    def test_empty_literal_evidence_is_refused(self):
        import copy
        ar=copy.deepcopy(self.ar);ar['items'][0]['evidence']['excerpt_id']=''
        with TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):render_held_editions(self.en,ar,slot_id=self.slot,output_dir=Path(tmp))
    def test_nonempty_output_not_overwritten(self):
        with TemporaryDirectory() as tmp:
            (Path(tmp)/'preserve').write_text('keep')
            with self.assertRaises(ValueError):render_held_editions(self.en,self.ar,slot_id=self.slot,output_dir=Path(tmp))
            self.assertEqual((Path(tmp)/'preserve').read_text(),'keep')
    def test_five_native_png_files_marked_no_post(self):
        from PIL import Image
        with TemporaryDirectory() as tmp:
            result=render_held_editions(self.en,self.ar,slot_id=self.slot,output_dir=Path(tmp))
            self.assertEqual(len(result['pages']),5)
            self.assertFalse(result['delivery_authorized'])
            self.assertFalse(result['discord_sent'])
            for rec in result['pages']:
                self.assertEqual(len(rec['sha256']),64)
                with Image.open(Path(tmp)/rec['path']) as img:
                    self.assertEqual(img.size,(3840,2160))

if __name__=='__main__':unittest.main()
