"""B64/B65 fail-closed audit and Somalia source evidence tests."""
import unittest
from v2_b64_b65_release_evidence import (
    AUDIT_COMMIT, AUDIT_RUN, AUDIT_STEPS, SOMALIA_CANDIDATES,
    verify_audit_receipt, reconcile_release_checks, qualify_somalia_candidates,
)

def receipt():
    return {"run_id": AUDIT_RUN, "head_sha": AUDIT_COMMIT, "branch": "main",
            "conclusion": "success",
            "steps": [{"name": s, "conclusion": "success"} for s in AUDIT_STEPS]}

class B64B65Tests(unittest.TestCase):
    def test_verified_audit_clears_only_audit_gate(self):
        result = reconcile_release_checks(
            {"production_source_audit_dependency_green": False,
             "independent_discord_client_receipts": False}, receipt())
        self.assertTrue(result["checks"]["production_source_audit_dependency_green"])
        self.assertEqual(result["open_release_blocks"], ["independent_discord_client_receipts"])
        self.assertFalse(result["can_release"])
    def test_wrong_commit_cannot_clear_gate(self):
        r = receipt(); r["head_sha"] = "0"*40
        self.assertFalse(verify_audit_receipt(r))
    def test_missing_successful_audit_step_cannot_clear_gate(self):
        r = receipt(); r["steps"][1]["conclusion"] = "failure"
        self.assertFalse(verify_audit_receipt(r))
    def test_self_asserted_audit_without_steps_denied(self):
        r = receipt(); r.pop("steps")
        self.assertFalse(verify_audit_receipt(r))
    def test_candidates_remain_disabled_and_unverified(self):
        result = qualify_somalia_candidates(SOMALIA_CANDIDATES)
        self.assertEqual(result["distinct_publishers"], 2)
        self.assertFalse(result["activation_allowed"])
        self.assertFalse(result["real_arabic_translation_verified"])
    def test_enabled_source_denied(self):
        candidates = [dict(x) for x in SOMALIA_CANDIDATES]
        candidates[0]["enabled"] = True
        with self.assertRaises(ValueError):
            qualify_somalia_candidates(candidates)
    def test_duplicate_publisher_denied(self):
        candidates = [dict(x) for x in SOMALIA_CANDIDATES]
        candidates[1]["publisher"] = "shabelle media"
        with self.assertRaises(ValueError):
            qualify_somalia_candidates(candidates)
    def test_unknown_language_denied(self):
        candidates = [dict(x) for x in SOMALIA_CANDIDATES]
        candidates[1]["language"] = "unknown"
        with self.assertRaises(ValueError):
            qualify_somalia_candidates(candidates)

if __name__ == "__main__":
    unittest.main()
