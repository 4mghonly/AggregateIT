"""B35 pure synthetic France24 parser-difference diagnostic tests."""
import json
import socket
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from v2_b35_france24_diagnostic import diagnose_bytes, main, SOURCE

OBSERVED = "2026-10-26T06:00:00+00:00"


def feed(links):
    items = "".join(
        "<item><title>" + title + "</title><link>" + url + "</link>"
        "<pubDate>Sun, 25 Oct 2026 05:00:00 GMT</pubDate>"
        "<description>Synthetic statement, not current news.</description></item>"
        for title, url in links
    )
    return ('<?xml version="1.0"?><rss version="2.0"><channel>'
            '<title>Controlled RSS</title>' + items + '</channel></rss>').encode("utf8")


NORMAL = feed([("First regional report", "https://example.org/article/a"),
               ("Second regional report", "https://example.org/article/b")])
DUPLICATE = feed([("First regional report", "https://example.org/article/a"),
                  ("Second regional report", "https://example.org/article/a")])


class ParserDiagnosticTests(unittest.TestCase):
    def test_normal_feed_has_exact_parity(self):
        r = diagnose_bytes(NORMAL, observed_at=OBSERVED)
        self.assertTrue(r["parity_on_new_capture"])
        self.assertEqual((r["v1_eligible"], r["v2_eligible"]), (2, 2))
        self.assertEqual(r["difference_classifications"], [])
        self.assertFalse(r["can_publish"])

    def test_duplicate_link_is_classified_and_redacted(self):
        r = diagnose_bytes(DUPLICATE, observed_at=OBSERVED)
        self.assertFalse(r["parity_on_new_capture"])
        self.assertEqual((r["v1_eligible"], r["v2_eligible"]), (2, 1))
        self.assertEqual(r["v2_rejected"]["duplicate_link"], 1)
        self.assertEqual(len(r["difference_classifications"]), 1)
        self.assertEqual(r["difference_classifications"][0]["classification"], "duplicate_link")
        self.assertNotIn("regional report", json.dumps(r))
        self.assertNotIn("https://example.org/article", json.dumps(r))
        self.assertTrue(r["reproduced_prior_one_item_difference"])
        self.assertFalse(r["historical_b34_bytes_replayed"])

    def test_raw_xml_entity_declaration_rejected(self):
        malicious = b"<!DOCTYPE rss [<!ENTITY x SYSTEM 'file:///etc/passwd'>]><rss/>"
        with self.assertRaises(ValueError):
            diagnose_bytes(malicious, observed_at=OBSERVED)

    def test_observation_time_required(self):
        with self.assertRaises(ValueError):
            diagnose_bytes(NORMAL, observed_at="2026-10-26T06:00:00")

    def test_single_fetch_and_metadata_only_artifact(self):
        with TemporaryDirectory() as d:
            out = Path(d) / "receipt.json"
            packet = {"status": 200, "final_url": SOURCE,
                      "content_type": "application/rss+xml", "body": DUPLICATE}
            with patch("v2_b35_france24_diagnostic.pinned_https_fetch", return_value=packet) as fetch:
                with patch("sys.argv", ["diagnostic", "--output", str(out)]):
                    self.assertEqual(main(), 0)
            self.assertEqual(fetch.call_count, 1)
            data = json.loads(out.read_text(encoding="utf8"))
            self.assertEqual(data["v1_only"], 1)
            self.assertEqual(data["http_status"], 200)
            self.assertNotIn("regional report", out.read_text(encoding="utf8"))
            self.assertTrue(data["no_raw_feed_artifact"])

    def test_comparison_never_uses_network(self):
        with (patch("socket.create_connection", side_effect=AssertionError("network")),
              patch("requests.get", side_effect=AssertionError("network"))):
            self.assertTrue(diagnose_bytes(NORMAL, observed_at=OBSERVED)["parity_on_new_capture"])


if __name__ == "__main__":
    unittest.main()
