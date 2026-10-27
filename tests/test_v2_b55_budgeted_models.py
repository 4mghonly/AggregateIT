"""B55 budgeted paid model selection: offline test stubs only."""
import json
import unittest
from v2_b55_budgeted_models import (CAP_USD,MODELS,authorized_model,
        conservative_reservation,execute,make_fixture)

def fake(url,*,headers,json,timeout,allow_redirects):
    model=json["model"]
    user=__import__("json").loads(json["messages"][1]["content"])
    class Resp:
        status_code=200
        def __init__(self):
            self.data={"choices":[{"message":{"content":__import__("json").dumps(
                {"items":[{"index":0,"source_sha256":user["source_sha256"],
                           "title_ar":"اقترح مسؤولون في الصومال 12 عيادة يوم 27 أكتوبر",
                           "summary_ar":"لم تتم الموافقة على الخطة ولم يتم افتتاح أي عيادة."}]},
                 ensure_ascii=False)}}],"usage":{"cost":0.0002}}
            self.content=b'{}'
        def json(self):return self.data
        def close(self):pass
    return Resp()
class Tests(unittest.TestCase):
    def test_exact_models_and_cost_bounds(self):
        self.assertEqual(set(MODELS),{"primary","fallback","referee"})
        with self.assertRaises(ValueError):authorized_model("not-authorized")
        self.assertLess(conservative_reservation("a"*1400,"referee"),0.02)
        self.assertEqual(CAP_USD,.5)
    def test_six_paid_requests_fit_strict_cap_without_publisher_text(self):
        result=execute(api_key="fixture-key",transport=fake)
        self.assertEqual(result["attempted_requests"],6)
        self.assertTrue(result["primary_fallback_both_contacted"])
        self.assertLess(result["reserved_upper_usd"],CAP_USD)
        self.assertEqual(result["reported_spend_usd"],.0012)
        self.assertFalse(result["source_backed_english_somali_translation_verified"])
        self.assertFalse(result["can_release"])
    def test_no_credentials_means_no_network_or_paid_spending(self):
        obj=execute(api_key="",transport=lambda *a,**k:self.fail("network"))
        self.assertEqual(obj["attempted_requests"],0)
    def test_invalid_scenarios_rejected(self):
        for x in [[("primary","en")]*2,[("nonfree","en")]]:
            with self.assertRaises(ValueError):
                execute(api_key="k",scenarios=x,transport=fake)
    def test_digest_mutation_rejected(self):
        def invalid(url,*,headers,json,timeout,allow_redirects):
            class R:
                status_code=200;content=b'{}'
                def json(self):
                    return {"choices":[{"message":{"content":__import__("json").dumps(
                        {"items":[{"index":0,"source_sha256":"0"*64,
                        "title_ar":"تقرير عن 12 عيادة في 27 أكتوبر",
                        "summary_ar":"لم يفتتح أي مركز."}]},ensure_ascii=False)}}],
                        "usage":{"cost":.0001}}
                def close(self):pass
            return R()
        out=execute(api_key="k",scenarios=[("primary","en")],transport=invalid)
        self.assertEqual(out["records"][0]["status"],"HOLD_QUALITY_GATE")
if __name__=="__main__":unittest.main()
