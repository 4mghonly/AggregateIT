"""Offline B6/B7 receipts and V1-V2 scorecard tests, no service connections."""
import copy
import unittest

from v2_delivery_gate import ReceiptGate
from v2_shadow_scorecard import compare_runs, validate_run

SLOT = "2026-10-23T06:00:00+04:00"
DIGEST = "a"*64


def run(product="arabic"):
    return {
        "product": product,
        "window_start": "2026-10-23T06:00:00+04:00",
        "window_end": "2026-10-23T12:00:00+04:00",
        "code_revision": "a"*40,
        "delivery_status": "not_attempted",
        "metrics": {
            "sources_attempted": 100, "sources_usable": 60,
            "events_selected": 12, "items_cited": 9,
            "items_rendered": 8, "translation_attempted": 10,
            "translation_succeeded": 5, "layout_omissions": 2,
            "clipped_items": 0,
        },
        "region_counts": {"gcc": 2, "yemen": 1},
    }


class ReceiptTests(unittest.TestCase):
    def test_en_ar_distinct_destinations(self):
        gate = ReceiptGate()
        self.assertTrue(gate.reserve(product="arabic",slot_id=SLOT,
                     destination_key="discord_webhook_arabic",edition_digest=DIGEST))
        self.assertTrue(gate.reserve(product="english",slot_id=SLOT,
                     destination_key="discord_webhook",edition_digest=DIGEST))
        self.assertEqual(gate.snapshot(product="english",slot_id=SLOT)["destination_key"],"discord_webhook")

    def test_wrong_channel_refused(self):
        with self.assertRaisesRegex(ValueError,"destination_mismatch"):
            ReceiptGate().reserve(product="arabic",slot_id=SLOT,
                     destination_key="discord_webhook",edition_digest=DIGEST)

    def test_idempotent_reservation_and_conflicting_payload_refused(self):
        gate = ReceiptGate()
        arg=dict(product="english",slot_id=SLOT,destination_key="discord_webhook",edition_digest=DIGEST)
        self.assertTrue(gate.reserve(**arg))
        self.assertFalse(gate.reserve(**arg))
        with self.assertRaisesRegex(ValueError,"different_content"):
            gate.reserve(**{**arg,"edition_digest":"b"*64})

    def test_ambiguous_network_timeout_blocks_retry(self):
        gate=ReceiptGate()
        gate.reserve(product="english",slot_id=SLOT,destination_key="discord_webhook",edition_digest=DIGEST)
        gate.mark_network_attempt(product="english",slot_id=SLOT)
        self.assertFalse(gate.retry_allowed(product="english",slot_id=SLOT))
        with self.assertRaises(ValueError):
            gate.mark_network_attempt(product="english",slot_id=SLOT)

    def test_receipt_is_caller_assertion_not_external_proof(self):
        gate=ReceiptGate()
        gate.reserve(product="arabic",slot_id=SLOT,destination_key="discord_webhook_arabic",edition_digest=DIGEST)
        gate.mark_network_attempt(product="arabic",slot_id=SLOT)
        gate.record_confirmed_receipt(product="arabic",slot_id=SLOT,
                     destination_key="discord_webhook_arabic",message_id="fake-123")
        row=gate.snapshot(product="arabic",slot_id=SLOT)
        self.assertEqual(row["state"],"confirmed_unverified")
        self.assertIn("requires_external",row["receipt_provenance"])
        self.assertFalse(gate.retry_allowed(product="arabic",slot_id=SLOT))

    def test_mismatched_receipt_not_allowed(self):
        gate=ReceiptGate()
        gate.reserve(product="arabic",slot_id=SLOT,destination_key="discord_webhook_arabic",edition_digest=DIGEST)
        gate.mark_network_attempt(product="arabic",slot_id=SLOT)
        with self.assertRaisesRegex(ValueError,"wrong_destination"):
            gate.record_confirmed_receipt(product="arabic",slot_id=SLOT,
                     destination_key="discord_webhook",message_id="fake-123")


class ScorecardTests(unittest.TestCase):
    def test_same_window_no_composite_claim(self):
        v1=run()
        v2=copy.deepcopy(v1)
        v2["metrics"]["items_cited"]=11
        v2["metrics"]["layout_omissions"]=0
        result=compare_runs(v1,v2)
        self.assertTrue(result["comparable"])
        self.assertEqual(result["metrics"]["items_cited"]["assessment"],"improved")
        self.assertEqual(result["metrics"]["layout_omissions"]["assessment"],"improved")
        self.assertEqual(result["factual_accuracy"],"not_measured")
        self.assertFalse(result["delivery_authorized"])

    def test_changed_window_not_comparable(self):
        v1=run();v2=copy.deepcopy(v1)
        v2["window_end"]="2026-10-23T18:00:00+04:00"
        self.assertFalse(compare_runs(v1,v2)["comparable"])

    def test_english_and_arabic_not_compared(self):
        self.assertFalse(compare_runs(run("english"),run("arabic"))["comparable"])

    def test_explicit_geographic_losses(self):
        v1=run(); v2=copy.deepcopy(v1)
        v2["region_counts"]={"gcc":2,"somalia":1}
        x=compare_runs(v1,v2)
        self.assertEqual(x["regions_lost"],["yemen"])
        self.assertEqual(x["regions_gained"],["somalia"])

    def test_contradictory_citation_counts_refused(self):
        bad=run();bad["metrics"]["items_cited"]=13
        with self.assertRaisesRegex(ValueError,"contradictory"):
            validate_run(bad)

    def test_extra_unapproved_raw_text_refused(self):
        bad=run();bad["article_text"]="private"
        with self.assertRaisesRegex(ValueError,"invalid_run_manifest"):
            validate_run(bad)

    def test_no_fake_model_evaluation(self):
        x=compare_runs(run(),run())
        self.assertEqual(x["source_rights"],"unverified")
        self.assertEqual(x["publisher_independence"],"unverified")
        self.assertEqual(x["status"],"offline_comparison_only")


if __name__ == "__main__":
    unittest.main()
