"""B34 no-post transport and artifact-redaction contract tests."""
import unittest
import socket
from unittest.mock import patch

import v2_b34_isolated_acceptance as b34


class IsolatedAcceptanceTests(unittest.TestCase):
    def test_only_registered_https_sources(self):
        self.assertEqual(len(b34.SOURCES), 4)
        self.assertEqual({p for p, _, _ in b34.SOURCES}, {"english", "arabic"})
        self.assertEqual(len({u for _, _, u in b34.SOURCES}), 4)
        self.assertTrue(all(u.startswith("https://") for _, _, u in b34.SOURCES))

    @patch.object(b34, "pinned_https_fetch")
    def test_one_network_error_yields_hold_and_no_retry(self, fetch):
        fetch.side_effect = socket.gaierror("offline")
        r = b34.probe(*b34.SOURCES[0])
        self.assertEqual(fetch.call_count, 1)
        self.assertEqual(r["failure_class"], "dns_resolution_failed")
        self.assertEqual(r["status"], "hold")
        self.assertFalse(r["discord_sent"])

    @patch.object(b34, "compare_imported_capture")
    @patch.object(b34, "pinned_https_fetch")
    def test_raw_body_never_appears_in_result(self, fetch, compare):
        raw = b"<rss>UNLICENSED-RAW-TEXT</rss>"
        fetch.return_value = {"body": raw, "final_url": b34.SOURCES[0][2],
                              "status": 200, "content_type": "application/rss+xml"}
        compare.return_value = {
            "stdlib_feedparser": {"feedparser_count": 2, "stdlib_count": 2,
                                  "missing_from_feedparser": [], "extra_in_feedparser": [],
                                  "parity_passed": True},
            "v1_v2_same_input": {"v1_parser_blob_verified": True,
                                "v1_extracted_count": 2, "v1_window_eligible": 2,
                                "v2_window_eligible": 2, "matching_items": 2,
                                "v1_only": [], "v2_only": [],
                                "parser_alignment": True}}
        r = b34.probe(*b34.SOURCES[0])
        self.assertEqual(r["status"], "compared")
        self.assertNotIn("UNLICENSED-RAW-TEXT", str(r))
        self.assertFalse(r["raw_body_artifact"])
        self.assertFalse(r["publisher_rights_verified"])
        receipt = compare.call_args.kwargs["receipt"]
        self.assertEqual(receipt["capture_kind"], "unattested_external_bytes")

    @patch.object(b34, "probe")
    def test_no_language_overclaim(self, probe):
        probe.side_effect = lambda product, label, url: {
            "product": product, "source_label": label, "status": (
                "compared" if product == "english" else "hold")}
        result = b34.run()
        self.assertFalse(result["english_arabic_capture_available"])
        self.assertEqual(result["operational_acceptance"], "HOLD")
        self.assertFalse(result["database_mutated"])

    def test_error_class_redacts_diagnostic_details(self):
        self.assertEqual(b34._error_type(ValueError("secret")), "unsafe_or_invalid_source")
        self.assertEqual(b34._error_type(RuntimeError("secret")), "parser_or_runtime_failed")


if __name__ == "__main__":
    unittest.main()
