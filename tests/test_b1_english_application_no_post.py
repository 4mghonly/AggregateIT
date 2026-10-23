"""B1/B3/B4/B5: actual English renderer fed by the source-bound V2 rehearsal."""
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from PIL import Image

from v2_english_application_rehearsal import (
    _render_data, main, rehearse_english, synthetic_fixture,
)
from v2_offline_rehearsal import run_offline_rehearsal


def registry():
    return {
        "schema_version": "2.0.0-preview",
        "sources": [{"id": i} for i in
                    ("en-001", "en-002", "en-003", "ar-s001", "ar-s019")],
    }


class EnglishApplicationNoPostTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.output = rehearse_english(synthetic_fixture(), registry())

    def test_real_production_format_renderer_accepts_only_english_admissions(self):
        self.assertEqual(self.output["selected"], 3)
        self.assertEqual(self.output["source_ids"], ["en-001", "en-002", "en-003"])
        self.assertEqual(self.output["held_reasons"], {"no_native_language_source": 1})
        self.assertEqual(len(self.output["pages"]), 2)
        for page in self.output["pages"]:
            self.assertEqual(sha256(page["png"]).hexdigest(), page["sha256"])
            with Image.open(BytesIO(page["png"])) as image:
                self.assertEqual(image.format, "PNG")
                self.assertEqual(image.size, (3840, 2160))

    def test_strict_no_delivery_or_claimed_real_source_quality(self):
        for field in ("live_collector_called", "live_model_called", "discord_sent", "database_written"):
            self.assertIs(self.output[field], False)
        self.assertEqual(self.output["publisher_rights"], "unverified")
        self.assertEqual(self.output["independent_reporting"], "unverified")
        self.assertEqual(self.output["market_data"], "unavailable")
        self.assertTrue(self.output["synthetic"])

    def test_render_adapter_does_not_invent_financials_severity_or_analysis(self):
        gate = run_offline_rehearsal(synthetic_fixture(), registry())
        data = _render_data(gate["products"]["english"]["plan"])
        self.assertTrue(data["sample"])
        self.assertEqual(data["pulse"], {"valid": False, "updated": None})
        self.assertEqual(data["macro"], {"valid": False, "updated": None})
        self.assertEqual(data["social_pulse"], {})
        self.assertTrue(all(e["severity"] == "Unrated" and e["confidence"] is None
                            and e["status"] == "UNVERIFIED" for e in data["events"]))

    def test_rejects_real_publisher_url_before_renderer(self):
        fixture = synthetic_fixture()
        fixture["documents"][0]["url"] = "https://www.reuters.com/example"
        with self.assertRaisesRegex(ValueError, "prohibits_real_article_urls"):
            rehearse_english(fixture, registry())

    def test_rejects_unmarked_real_material(self):
        fixture = synthetic_fixture()
        fixture["synthetic"] = False
        with self.assertRaisesRegex(ValueError, "requires_explicit_synthetic"):
            rehearse_english(fixture, registry())

    def test_no_native_english_evidence_means_no_render(self):
        fixture = synthetic_fixture()
        for d in fixture["documents"]:
            if d["original_language"] == "en":
                d["original_language"] = "fr"
        with self.assertRaisesRegex(ValueError, "no_native_english_excerpt_to_render"):
            rehearse_english(fixture, registry())

    def test_cli_refuses_overwrite_before_rendering(self):
        with TemporaryDirectory() as dirname:
            file = Path(dirname) / "english-v2-synthetic-page-1.png"
            file.write_bytes(b"existing-user-data")
            with patch("sys.stderr"):
                with self.assertRaises(SystemExit) as exc:
                    main(["--output", dirname])
            self.assertEqual(exc.exception.code, 2)
            self.assertEqual(file.read_bytes(), b"existing-user-data")


if __name__ == "__main__":
    unittest.main()
