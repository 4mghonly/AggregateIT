import unittest
from v2_b45_free_live_models import free_route_guard,run_probe

def route(model="openrouter/free",base="https://openrouter.ai/api/v1"):
    return {"base":base,"model":model,"chat":"/chat/completions","key":"nonsecret-fixture","options":{}}
def reply(r,sys,data,max_tokens):
    original=data["items"][0]
    title=("ناقش مسؤولون صوماليون خطة 12 عيادة يوم 27 أكتوبر" if original["language"]=="en"
           else "ناقش مسؤولون في الصومال خطة 12 مركزاً يوم 27 أكتوبر")
    return {"items":[{"index":0,"source_sha256":original["source_sha256"],
        "title_ar":title,"summary_ar":"لم يتم تأكيد الافتتاح، وكان الأمر مجرد خطة."}]}
class B45Probe(unittest.TestCase):
    def test_nonfree_or_nonopenrouter_refused(self):
        self.assertNotEqual(free_route_guard(route(model="glm-5.3")),"FREE_ROUTE_CONFIGURED")
        self.assertNotEqual(free_route_guard(route(base="https://example.com/api/v1")),"FREE_ROUTE_CONFIGURED")
    def test_free_model_structurally_checked_not_semantically_proven(self):
        r=run_probe(primary=route(),fallback=route(),caller=reply,resolve_env=False)
        self.assertEqual(r["actual_free_provider_attempts"],3)
        self.assertTrue(r["english_structural_pass"]);self.assertTrue(r["somali_structural_pass"])
        self.assertFalse(r["independent_semantic_quality_verified"])
        self.assertFalse(r["can_release"])
    def test_nonfree_fallback_never_called(self):
        r=run_probe(primary=route(),fallback=route(model="glm-5.3"),caller=reply,resolve_env=False)
        self.assertEqual(r["actual_free_provider_attempts"],2)
        self.assertFalse(r["real_fallback_endpoint_tested"])
    def test_no_config_means_no_model_call(self):
        r=run_probe(primary={},fallback={},caller=lambda *a,**k:self.fail("called"),resolve_env=False)
        self.assertEqual(r["actual_free_provider_attempts"],0)
    def test_unbound_digest_and_changed_number_rejected(self):
        def bad(r,s,p,max_tokens):
            x=reply(r,s,p,max_tokens);x["items"][0]["source_sha256"]="0"*64
            x["items"][0]["title_ar"]=x["items"][0]["title_ar"].replace("12","13")
            return x
        r=run_probe(primary=route(),fallback={},caller=bad,resolve_env=False)
        self.assertFalse(r["english_structural_pass"])
if __name__=="__main__":unittest.main()
