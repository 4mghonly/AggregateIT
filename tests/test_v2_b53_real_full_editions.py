"""B53/B54 immutable genuinely archived final-page inventory and strict release HOLD."""
import unittest,json
from io import BytesIO
from zipfile import ZipFile,ZIP_DEFLATED
from PIL import Image
from v2_b53_authentic_full_editions import (
    inspect_original_final_edition,assess_original_final_pair,
    EXPECTED_ORIGINALS,decide_acceptance)
from hashlib import sha256

def zips(product):
    buf=BytesIO()
    with ZipFile(buf,'w',compression=ZIP_DEFLATED) as z:
        if product=='english':
            z.writestr('gazette_health.json',json.dumps({'status':'degraded','llm_ok':False,
                'delivery':{'confirmed':True}}))
            names=['intel_slide_p1.png','intel_slide_p2.png']
        else:
            z.writestr('health.json',json.dumps({'translation':{'requested_foreign':8,
                'translated_foreign':2,'routes':[{'route':'fallback','error':'http_403'}]},
                'delivery':{'confirmed':True}}))
            z.writestr('briefing.json',json.dumps({'schema_version':'arabic-brief-v3',
                'sample':False,'window_start':'2026-10-27T12:08:46+04:00',
                'window_end':'2026-10-27T18:08:46+04:00','events':[{'id':'fixture'}]}))
            names=['arabic-p1.png','arabic-p2.png','arabic-p3.png']
        for filename in names:
            png=BytesIO();Image.new('RGB',(3840,2160),(40,50,60)).save(png,format='PNG')
            z.writestr(filename,png.getvalue())
    return buf.getvalue()

class GenuineOriginals(unittest.TestCase):
    def inspect(self,p):
        raw=zips(p)
        return inspect_original_final_edition(raw,product=p,
                 run_id=EXPECTED_ORIGINALS[p]['run_id'],expected_zip_sha256=sha256(raw).hexdigest())
    def test_genuine_english_final_2_pages_and_degraded_llm(self):
        r=self.inspect('english')
        self.assertEqual(r['native_page_count'],2)
        self.assertFalse(r['llm_ok'])
        self.assertTrue(r['app_claimed_delivery'])
        self.assertFalse(r['independent_discord_client_receipt'])
    def test_genuine_arabic_3_pages_and_translation_not_full(self):
        r=self.inspect('arabic')
        self.assertEqual(r['native_page_count'],3)
        self.assertEqual((r['foreign_translation_requested'],r['foreign_translation_completed']),(8,2))
        self.assertGreaterEqual(r['fallback_http_403'],1)
        self.assertFalse(r['translation_complete'])
    def test_zip_digest_required_and_unsafe_paths_fail(self):
        x=zips('english')
        with self.assertRaisesRegex(ValueError,'original_zip_digest_mismatch'):
            inspect_original_final_edition(x,product='english',run_id=EXPECTED_ORIGINALS['english']['run_id'],
                                           expected_zip_sha256='0'*64)
        buf=BytesIO()
        with ZipFile(buf,'w') as z:z.writestr('../bad.png','bad')
        with self.assertRaises(ValueError):
            inspect_original_final_edition(buf.getvalue(),product='english',
                   run_id=EXPECTED_ORIGINALS['english']['run_id'],
                   expected_zip_sha256=sha256(buf.getvalue()).hexdigest())
    def test_new_english_pages_do_not_fabricate_same_window(self):
        result=assess_original_final_pair([self.inspect('english'),self.inspect('arabic')],
              v2_observed_at='2026-10-27T09:15:59.555886+00:00')
        self.assertTrue(result['both_original_products_have_4k_pages'])
        self.assertEqual(result['matched_v1_v2_full_edition_slots'],0)
        self.assertFalse(result['source_bytes_replayable'])
        self.assertFalse(result['can_release'])
    def test_forged_release_refused(self):
        rows=[self.inspect('english'),self.inspect('arabic')]
        rows[0]['can_release']=True
        with self.assertRaises(ValueError):
            assess_original_final_pair(rows,v2_observed_at='2026-10-27T09:15:59.555886+00:00')
    def test_no_credentials_no_canary_even_when_both_original_images_exist(self):
        match=assess_original_final_pair([self.inspect('english'),self.inspect('arabic')],
              v2_observed_at='2026-10-27T09:15:59.555886+00:00')
        gate=decide_acceptance(match,source_audit_healthy=False)
        self.assertIn('b45_real_translation_and_independent_fallback_not_accepted',gate['critical_blockers'])
        self.assertIn('full_edition_v1_v2_same_slot_source_bytes_missing',gate['critical_blockers'])
        self.assertIn('production_source_audit_not_green',gate['critical_blockers'])
        self.assertFalse(gate['canary_authorized'])
        self.assertFalse(gate['can_release'])
    def test_missing_source_audit_status_cannot_be_assumed_healthy(self):
        result=assess_original_final_pair([self.inspect('english'),self.inspect('arabic')],
              v2_observed_at='2026-10-27T09:15:59.555886+00:00')
        gate=decide_acceptance(result,source_audit_healthy=None)
        self.assertEqual(gate['source_audit_status'],'NOT_INDEPENDENTLY_VERIFIED')
if __name__=='__main__':unittest.main()
