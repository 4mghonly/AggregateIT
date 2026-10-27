"""Original V1 artifact inventory: no synthetic V1 data can close full B49."""
import json,unittest,zipfile
from io import BytesIO
from PIL import Image
from v2_b49_archived_edition_gate import inspect_original_zip,assess_original_vs_v2

def archive(product,*,full=True):
    m=BytesIO()
    with zipfile.ZipFile(m,'w',compression=zipfile.ZIP_DEFLATED) as z:
        if product=='arabic':
            trans={'requested_foreign':8,'translated_foreign':3,
                   'routes':[{'route':'fallback','error':'http_403'}]}
            z.writestr('health.json',json.dumps({'translation':trans,'delivery':{'confirmed':True}}))
            z.writestr('briefing.json',json.dumps({'schema_version':'arabic-brief-v3',
                'sample':False,'window_start':'2026-10-27T06:00:00+04:00',
                'window_end':'2026-10-27T12:00:00+04:00','events':[{}]}))
            for i in range(1,4 if full else 3):
                buf=BytesIO();Image.new('RGB',(3840,2160)).save(buf,format='PNG')
                z.writestr('arabic-p'+str(i)+'.png',buf.getvalue())
        else:
            z.writestr('health.json',json.dumps({'overall':'YELLOW','degraded':['LLM API failure']}))
            z.writestr('run.json',json.dumps({'run':'2026-10-27T09:11:00+00:00',
                'dry_run':False,'fetched':503,'events':[{}]}))
            z.writestr('token_usage.json','{}')
    return m.getvalue()
class GenuineV1Tests(unittest.TestCase):
    def test_two_original_artifacts_hold_due_to_missing_english_native_and_translation(self):
        ar=inspect_original_zip(archive('arabic'),product='arabic',run_id=40471115356)
        en=inspect_original_zip(archive('english'),product='english',run_id=40478745761)
        report=assess_original_vs_v2([ar,en],v2_observed_at='2026-10-27T09:15:59+00:00')
        self.assertEqual(report['arabic_v1_png_count'],3)
        self.assertEqual(report['english_v1_png_count'],0)
        self.assertIn('production_arabic_fallback_http_403',report['critical_blockers'])
        self.assertFalse(report['can_release'])
    def test_missing_original_4k_is_refused(self):
        with self.assertRaisesRegex(ValueError,'missing_original_arabic_pages'):
            inspect_original_zip(archive('arabic',full=False),product='arabic',run_id=40471115356)
    def test_untrusted_pair_refused(self):
        with self.assertRaises(ValueError):
            assess_original_vs_v2([],v2_observed_at='2026-10-27T09:15:59+00:00')
if __name__=='__main__':unittest.main()
