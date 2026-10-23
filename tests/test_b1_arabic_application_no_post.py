"""Actual three-slide Arabic renderer follows V2 native-source gate, NO POST."""
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from PIL import Image

from v2_arabic_application_rehearsal import (
    _render_brief, arabic_synthetic_fixture, main, rehearse_arabic,
)
from v2_offline_rehearsal import run_offline_rehearsal
from arabic_layout.render_engine import severity


def registry():
    return {"schema_version": "2.0.0-preview", "sources": [
        {"id": x} for x in ("en-001", "en-002", "en-003", "ar-s001",
                            "ar-s002", "ar-s003", "ar-s019")
    ]}


class ArabicApplicationNoPostTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = arabic_synthetic_fixture()
        cls.output = rehearse_arabic(cls.fixture, registry())

    def test_genuine_arabic_renderer_produces_three_evidence_gated_pages(self):
        self.assertEqual(self.output["selected"], 3)
        self.assertEqual(self.output["source_ids"], ["ar-s001", "ar-s002", "ar-s003"])
        self.assertEqual(len(self.output["pages"]), 3)
        for page in self.output["pages"]:
            self.assertEqual(sha256(page["png"]).hexdigest(), page["sha256"])
            with Image.open(BytesIO(page["png"])) as image:
                self.assertEqual(image.format, "PNG")
                self.assertEqual(image.size, (3840, 2160))

    def test_exact_quotes_and_no_fabricated_translation_assessment_or_severity(self):
        gate = run_offline_rehearsal(self.fixture, registry())
        plan = gate["products"]["arabic"]["plan"]
        brief = _render_brief(plan, self.fixture)
        self.assertEqual({e["title_ar"] for e in brief["events"]},
                         {i["evidence"]["quote"] for i in plan["items"]})
        self.assertTrue(all(e["severity"] == "unknown" and not e["assessment_ar"]
                            and not e["watch_ar"] for e in brief["events"]))
        self.assertEqual(self.output["translation"], "not_attempted")
        self.assertEqual(self.output["analysis"], "abstained_unverified")
        self.assertEqual(severity({"severity": "unknown"})[0], "غير مصنف")
        self.assertEqual(severity({"severity": "low"})[0], "منخفض")
        self.assertEqual(severity({})[0], "غير مصنف")

    def test_no_service_write_or_validated_publisher_inference(self):
        for key in ("real_collector_called", "live_model_called", "discord_sent", "database_written"):
            self.assertIs(self.output[key], False)
        self.assertEqual(self.output["publisher_rights"], "unverified")
        self.assertEqual(self.output["independent_reporting"], "unverified")
        self.assertTrue(self.output["synthetic"])

    def test_non_arabic_only_input_is_withheld_not_rendered(self):
        fixture = arabic_synthetic_fixture()
        for row in fixture["documents"]:
            if row["original_language"] == "ar":
                row["original_language"] = "fa"
        with self.assertRaisesRegex(ValueError, "no_native_arabic_excerpt_to_render"):
            rehearse_arabic(fixture, registry())

    def test_wrong_script_under_arabic_label_refused(self):
        fixture = arabic_synthetic_fixture()
        for row in fixture["documents"]:
            if row["original_language"] == "ar":
                row["original_text"] = "A completely fabricated English statement for the test."
                row["excerpt_end"] = len(row["original_text"])
        with self.assertRaisesRegex(ValueError, "no_native_arabic_excerpt_to_render"):
            rehearse_arabic(fixture, registry())

    def test_real_source_url_rejected_before_renderer(self):
        fixture = arabic_synthetic_fixture()
        fixture["documents"][1]["url"] = "https://www.bbc.com/example"
        with self.assertRaisesRegex(ValueError, "prohibits_real_article_urls"):
            rehearse_arabic(fixture, registry())

    def test_cli_does_not_overwrite_user_file(self):
        with TemporaryDirectory(prefix="aggregateit-v2-arabic-overwrite-") as dirname:
            path = Path(dirname) / "arabic-v2-synthetic-page-1.png"
            path.write_bytes(b"keep_existing")
            with patch("sys.stderr"):
                with self.assertRaises(SystemExit) as exc:
                    main(["--output", dirname])
            self.assertEqual(exc.exception.code, 2)
            self.assertEqual(path.read_bytes(), b"keep_existing")


if __name__ == "__main__":
    unittest.main()
