"""B66-B71 offline, fail-closed evidence regressions."""
import unittest
from v2_b66_b71_evidence import *
class EvidenceTests(unittest.TestCase):
    def test_b66_empty_source_floor(self):
        self.assertFalse(b66_sources([])["technical_floor_met"])
    def test_b66_duplicate_publisher_not_two(self):
        r={"publisher":"Same","http_status":200,"parse_compatible":True,"fresh_items":2,
           "observed_from_live_fetch":True,"response_sha256":"a"*64}
        self.assertEqual(b66_sources([r,r])["compatible_distinct_sources"],1)
    def test_b66_two_independent_sources_do_not_activate(self):
        a={"publisher":"A","http_status":200,"parse_compatible":True,"fresh_items":1,
           "observed_from_live_fetch":True,"response_sha256":"a"*64}
        b=dict(a,publisher="B")
        result=b66_sources([a,b]);self.assertTrue(result["technical_floor_met"])
        self.assertFalse(result["activation_allowed"])
    def test_b67_no_unverified_semantic_acceptance(self):
        self.assertFalse(b67_translation([{"original_language":"so"}])["publisher_story_semantic_fidelity_verified"])
    def test_b68_unreviewed_visuals_held(self):
        self.assertEqual(len(b68_visual([],{})["outstanding_defects"]),5)
    def test_b69_empty_week_missing_seven_each(self):
        r=b69_week([],"2026-10-28T18:00:00+04:00")
        self.assertEqual(len(r["missing_days"]["arabic"]),7)
    def test_b70_same_source_is_not_full_parity(self):
        d="a"*64
        r=b70_parity([{"same_utc_slot":True,"source_sha256":d,
                        "v1_source_sha256":d,"v2_source_sha256":d,
                        "v1_edition_sha256":d,"v2_edition_sha256":d}])
        self.assertEqual(r["same_source_pairs"],1)
        self.assertFalse(r["full_editorial_model_render_delivery_parity_verified"])
    def test_b71_no_self_attested_delivery(self):
        r=b71_delivery([{"ok":True}],[{"delivered":True}])
        self.assertFalse(r["independent_discord_client_receipts_verified"])
    def test_full_execution_no_post(self):
        r=execute_all();self.assertFalse(r["can_release"])
        self.assertEqual(r["paid_calls"],0)
        self.assertFalse(r["discord_sent"])
if __name__=="__main__":unittest.main()
