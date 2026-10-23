"""B2 triage: no live access or invented publisher validation."""
import copy
import unittest
from v2_source_gate import source_gate_report

# The shipped registry is read-only; no test depends on current website uptime.
class SourceGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            cls.registry = FULL_REGISTRY  # injected only by memory-only verification harness
        except NameError:
            import json
            from pathlib import Path
            path = Path(__file__).resolve().parents[1] / "config" / "v2" / "source_registry.json"
            cls.registry = json.loads(path.read_text(encoding="utf-8"))

    def test_five_high_risk_areas_triaged(self):
        r=source_gate_report(self.registry)
        self.assertEqual(set(r["areas"]), {"somalia","yemen","egypt","jordan","uae"})
        self.assertEqual(r["registry_source_ids"],222)

    def test_all_gates_remain_on_hold(self):
        r=source_gate_report(self.registry)
        self.assertEqual(r["gate_status"],"hold_unverified_live_rights_independence")
        for area in r["areas"].values():
            self.assertFalse(area["ready"])
            self.assertEqual(area["verified_independent_families"],0)

    def test_no_live_requests_or_promotions_claimed(self):
        r=source_gate_report(self.registry)
        self.assertEqual(r["live_requests_made"],0)
        self.assertEqual(r["sources_promoted"],0)
        self.assertEqual(r["publisher_rights_verified"],0)

    def test_bounded_unique_host_queue(self):
        r=source_gate_report(self.registry)
        for area in r["areas"].values():
            queue=area["bounded_probe_queue"]
            self.assertLessEqual(len(queue),2)
            self.assertEqual(len({x["host_candidate"] for x in queue}),len(queue))
            for candidate in queue:
                self.assertEqual(candidate["live_probe"],"not_attempted")
                self.assertEqual(candidate["rights"],"unreviewed")
                self.assertEqual(candidate["independent_publisher_family"],"unverified")

    def test_known_historical_gaps_present(self):
        r=source_gate_report(self.registry)
        for key in ("somalia","yemen","egypt","jordan"):
            self.assertIn("historical_dated_recent_below_floor",r["areas"][key]["gap_flags"])
        self.assertIn("distinct_host_candidates_below_floor",r["areas"]["uae"]["gap_flags"])

    def test_publisher_host_duplicate_not_counted_as_independent(self):
        r=source_gate_report(self.registry)
        ids={x["id"] for x in r["areas"]["uae"]["bounded_probe_queue"]}
        self.assertLessEqual(len(ids),2)
        self.assertEqual(r["areas"]["uae"]["historical_distinct_host_candidates"],2)
        self.assertEqual(r["areas"]["uae"]["verified_independent_families"],0)

    def test_missing_source_id_detected_in_snapshot(self):
        r=copy.deepcopy(self.registry)
        r["sources"]=[x for x in r["sources"] if x["id"]!="ar-s056"]
        with self.assertRaisesRegex(ValueError,"coverage_snapshot_disagrees"):
            source_gate_report(r)

    def test_duplicate_id_refused(self):
        r=copy.deepcopy(self.registry)
        r["sources"].append(copy.deepcopy(r["sources"][0]))
        with self.assertRaisesRegex(ValueError,"duplicate_source_ids"):
            source_gate_report(r)

    def test_strict_probe_ceiling(self):
        with self.assertRaisesRegex(ValueError,"bounded_probe_limit"):
            source_gate_report(self.registry,max_live_candidates_per_area=3)

    def test_non_versioned_registry_rejected(self):
        r=copy.deepcopy(self.registry)
        r["schema_version"]="unknown"
        with self.assertRaisesRegex(ValueError,"requires_pinned_registry"):
            source_gate_report(r)

if __name__=="__main__":
    unittest.main()
