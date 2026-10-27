"""B59-62 TDD guards for translation, real layout, seven-day lineage, release HOLD."""
import unittest
from datetime import datetime,timedelta,timezone
from v2_b59_semantic_guard import fixture_digest,inspect_known_translation
from v2_b60_original_edition_qa import KNOWN_DEFECTS,inspect_layout_geometry,assess_original_visual_status
from v2_b61_week_lineage import evaluate_week_lineage
from v2_b62_precanary import evaluate_precanary

def good_translation():
    return inspect_known_translation("en-plan",
       "اقترح مسؤولون في الصومال 12 عيادة في 27 أكتوبر",
       "لم تتم الموافقة على الخطة ولم يتم تأكيد افتتاح أي عيادة.",
       original_sha256=fixture_digest("en-plan"))
def visuals():
    return {"schema":"aggregateit-v2-b53-original-visual-inventory/1",
             "known_defects":list(KNOWN_DEFECTS)}
def pages():
    return [{"product":p,"page":i,"width":3840,"height":2160,
             "sha256":"a"*64,"boxes":[{"x":50,"y":60,"w":700,"h":60,"font_px":34}]}
            for p,n in (("english",2),("arabic",3)) for i in range(1,n+1)]
def empty_week():return evaluate_week_lineage([],as_of="2026-10-27T18:00:00+04:00")
def config():
    return {"schema":"aggregateit-v2-b58-model-selection/1",
      "api_base":"https://openrouter.ai/api/v1","key_secret_name":"LLM_API_KEY",
      "primary":{"model":"google/gemini-3.1-flash-lite","family":"google"},
      "fallback":{"model":"openai/gpt-oss-120b","family":"openai"},
      "budget":{"approved_usd":0.5,"spent_reported_b55_b56_b57_usd":0.0024507,
                "conservative_reserved_b55_b56_b57_usd":0.101496},
      "activation":{"enabled":False,"production_model_changes_authorized":False,
        "full_real_news_source_translation_accepted":False,"live_primary_outage_proven":False,
        "translated_publisher_rights_verified":False,"full_original_v1_v2_same_slot_proven":False,
        "discord_client_receipts_verified":False}}
class B59Tests(unittest.TestCase):
    def test_expected_negation_and_numbers_pass_synthetic_only(self):
        a=good_translation();self.assertTrue(a["checks_passed"])
        self.assertFalse(a["publisher_story_semantic_fidelity_verified"])
    def test_fabricated_opening_or_missing_negation_is_held(self):
        a=inspect_known_translation("en-plan","افتتحت بالفعل 12 عيادة في 27 أكتوبر",
              "تمت الموافقة على الخطة.",original_sha256=fixture_digest("en-plan"))
        self.assertFalse(a["checks_passed"])
        self.assertIn("invented_confirmation",a["issues"])
    def test_quantity_mutation_and_unbound_digest_fail(self):
        a=inspect_known_translation("so-plan","توجد خطة 13 مركزاً يوم 27 أكتوبر",
           "لم تتم الموافقة.",original_sha256=fixture_digest("so-plan"))
        self.assertIn("numbers_mismatched",a["issues"])
        with self.assertRaises(ValueError):
            inspect_known_translation("en-plan","خطة 12","لم يتم 27",original_sha256="0"*64)
class B60Tests(unittest.TestCase):
    def test_technical_boxes_can_pass_without_editorial_clearance(self):
        a=assess_original_visual_status(original_manifest=visuals(),candidate_geometry=pages())
        self.assertEqual(a["candidate_geometry"]["violations"],[])
        self.assertFalse(a["editorial_and_visual_defects_resolved"])
    def test_clipping_and_tiny_font_detected(self):
        p=pages();p[0]["boxes"][0].update(x=3800,w=90,font_px=19)
        v=inspect_layout_geometry(p)
        self.assertIn("text_box_clipped",v["violations"])
        self.assertIn("too_small_at_4k",v["violations"])
    def test_missing_original_defect_cannot_be_marked_clear(self):
        a=visuals();a["known_defects"].pop()
        with self.assertRaises(ValueError):assess_original_visual_status(original_manifest=a)
class B61Tests(unittest.TestCase):
    def test_single_day_not_full_week(self):
        v=empty_week();self.assertEqual(v["observed_days"],{"english":0,"arabic":0})
        self.assertFalse(v["seven_distinct_days_structurally_present"])
    def test_two_language_distinct_days_not_claimed_delivered(self):
        base=datetime(2026,10,27,18,tzinfo=timezone(timedelta(hours=4)))
        rows=[]
        for p in ("english","arabic"):
            for i in range(7):
                day=base-timedelta(days=i)
                rows.append({"product":p,"slot_id":day.isoformat(),"origin":"original_source_capture",
                    "held":True,"production_sent":False,
                    "edition_sha256":format(1+len(rows),"064x"),
                    "source_snapshot_sha256":format(100+len(rows),"064x")})
        v=evaluate_week_lineage(rows,as_of=base.isoformat())
        self.assertTrue(v["seven_distinct_days_structurally_present"])
        self.assertFalse(v["full_real_weekly_editorial_quality_verified"])
        self.assertFalse(v["can_release"])
    def test_duplicate_day_timezone_equivalence_denied(self):
        rows=[{"product":"arabic","slot_id":"2026-10-27T18:00:00+04:00",
               "origin":"original_source_capture","held":True,"production_sent":False,
               "edition_sha256":"a"*64,"source_snapshot_sha256":"b"*64}]
        rows.append({**rows[0],"slot_id":"2026-10-27T14:00:00Z",
                     "edition_sha256":"c"*64})
        with self.assertRaisesRegex(ValueError,"duplicate_daily_product_date"):
            evaluate_week_lineage(rows,as_of="2026-10-27T19:00:00+04:00")
class B62Tests(unittest.TestCase):
    def test_no_false_canary_even_with_structural_fixture_success(self):
        r=evaluate_precanary(config(),b59=good_translation(),
            b60=assess_original_visual_status(original_manifest=visuals()),
            b61=empty_week())
        self.assertEqual(r["release_status"],"HOLD")
        self.assertFalse(r["can_release"])
        self.assertEqual(r["new_paid_calls"],0)
        self.assertIn("b49_same_slot_full_v1_v2_model_editorial_render_delivery",r["open_release_blocks"])
    def test_caller_assertion_cannot_skip_independent_receipts(self):
        with self.assertRaisesRegex(ValueError,"self_asserted_live_acceptance"):
            evaluate_precanary(config(),b59=good_translation(),
               b60=assess_original_visual_status(original_manifest=visuals()),
               b61=empty_week(),attestation={"independent_discord_client_receipts":True})
    def test_model_configuration_activation_refused(self):
        c=config();c["activation"]["enabled"]=True
        with self.assertRaises(ValueError):
            evaluate_precanary(c,b59=good_translation(),
              b60=assess_original_visual_status(original_manifest=visuals()),b61=empty_week())
if __name__=="__main__":unittest.main()
