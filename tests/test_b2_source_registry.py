"""B2 snapshot tests; standard library only, no requests, no hosted resources."""
import copy
import unittest

from v2_sources import load_inputs, validate_registry


class RegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry, cls.english, cls.arabic, cls.audit = load_inputs()

    def _errors(self, modified):
        return validate_registry(modified, self.english, self.arabic, self.audit)

    def test_snapshot_matches_three_sources(self):
        self.assertEqual(self._errors(self.registry), [])

    def test_all_222_sources_have_distinct_stable_ids(self):
        rows = self.registry["sources"]
        self.assertEqual((len(rows), len(set(r["id"] for r in rows))), (222, 222))
        self.assertEqual(sum(r["stream"] == "english" for r in rows), 104)
        self.assertEqual(sum(r["stream"] == "arabic" for r in rows), 118)

    def test_repeated_id_rejected(self):
        r = copy.deepcopy(self.registry)
        r["sources"][1]["id"] = r["sources"][0]["id"]
        self.assertIn("duplicate_ids", self._errors(r))

    def test_changed_source_url_rejected(self):
        r = copy.deepcopy(self.registry)
        r["sources"][0]["entrypoint"] = "https://invalid.example/rss"
        self.assertIn("english_source_drift:en-001", self._errors(r))

    def test_disabled_english_source_stays_disabled(self):
        row = next(r for r in self.registry["sources"] if r["legacy_id"] == 68 and r["stream"] == "english")
        self.assertEqual(row["legacy_state"], "disabled")
        r = copy.deepcopy(self.registry)
        next(x for x in r["sources"] if x["id"] == row["id"])["legacy_state"] = "claimed_active"
        self.assertIn(f"english_source_drift:{row['id']}", self._errors(r))

    def test_unverified_english_source_not_promoted(self):
        rows = [r for r in self.registry["sources"] if r["stream"] == "english" and r["legacy_state"] == "unverified"]
        self.assertEqual(len(rows), 13)
        self.assertNotIn("language", rows[0])

    def test_shared_feed_links_are_not_independent_sources(self):
        duplicate_urls = self.registry["shared_feed_urls"]
        self.assertEqual(len(duplicate_urls), 8)
        for x in duplicate_urls:
            self.assertEqual({s.split("-")[0] for s in x["source_ids"]}, {"en", "ar"})

    def test_repository_links_never_treated_as_rss(self):
        github = [r for r in self.registry["sources"] if r["stream"] == "english" and r["entrypoint_type"] == "discovery_only"]
        self.assertEqual(len(github), 5)

    def test_html_adapters_pass_audit_without_measured_freshness(self):
        row = next(r for r in self.registry["sources"] if r["id"] == "ar-s070")
        self.assertEqual(row["entrypoint_type"], "html_headlines")
        self.assertEqual(row["observed"]["dated_72h"], 0)
        self.assertTrue(row["observed"]["compatible"])

    def test_somalia_historical_source_gap_exposed(self):
        cov = next(c for c in self.registry["coverage"]["arabic_regions"] if c["region"] == "somalia")
        self.assertEqual((cov["historical_adapter_compatible"], cov["historical_dated_recent"]), (1, 1))
        self.assertIn("historical_compatible_below_floor", cov["gaps"])

    def test_uae_host_families_not_certified(self):
        cov = self.registry["coverage"]["uae_country"]
        self.assertEqual((cov["historical_adapter_compatible"], cov["historical_dated_recent"]), (7, 3))
        self.assertEqual(cov["distinct_host_candidates_with_dated_recent"], 2)
        self.assertEqual(cov["verified_independent_families"], 0)

    def test_cannot_forge_geographic_floor(self):
        r = copy.deepcopy(self.registry)
        r["coverage"]["uae_country"]["verified_independent_families"] = 3
        self.assertIn("uae_coverage_drift", self._errors(r))

    def test_cannot_forge_freshness_counts(self):
        r = copy.deepcopy(self.registry)
        next(x for x in r["sources"] if x["id"] == "ar-s070")["observed"]["dated_72h"] = 20
        self.assertIn("probe_recent:ar-s070", self._errors(r))

    def test_cannot_silently_rewrite_historic_audit(self):
        r = copy.deepcopy(self.registry)
        r["sources_of_record"]["arabic_audit_checked_at"] = "2026-10-23"
        self.assertIn("audit_date_drift", self._errors(r))


if __name__ == "__main__":
    unittest.main()
