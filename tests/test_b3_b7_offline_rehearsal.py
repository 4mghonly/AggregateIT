"""Genuine module-collaboration rehearsal, but with ONLY synthetic inputs."""
import copy
import unittest

from v2_offline_rehearsal import run_offline_rehearsal

STAMP = "2026-10-23T08:00:00+00:00"
SLOT = "2026-10-23T12:00:00+04:00"


def row(source_id, language, text, url, key="synthetic.same-event",
        region="gcc", country="AE", topic_en="geopolitics", topic_ar="security"):
    return {
        "source_id": source_id, "url": url, "original_text": text,
        "original_language": language, "retrieved_at": STAMP,
        "published_at": STAMP, "excerpt_start": 0, "excerpt_end": len(text),
        "claim_statement": "Attributed synthetic example: " + text,
        "explicit_event_key": key, "region": region,
        "subject_country": country, "topic_english": topic_en,
        "topic_arabic": topic_ar, "priority": 80,
    }


def fixture():
    return {
        "schema": "aggregateit-v2-offline-rehearsal/1", "synthetic": True,
        "as_of": STAMP, "slot_id": SLOT,
        "documents": [
            row("en-001", "en", "Synthetic station reported a test update.",
                "https://sample.invalid/english"),
            row("ar-s001", "ar", "أعلنت محطة تجريبية تحديثاً للاختبار.",
                "https://sample.invalid/arabic"),
            row("ar-s019", "fa", "گزارش آزمایشی منتشر شد.",
                "https://sample.invalid/persian", key="synthetic.iran-foreign",
                region="iran", country="IR"),
        ],
    }


def registry():
    return {
        "schema_version": "2.0.0-preview",
        "sources": [{"id":"en-001"},{"id":"ar-s001"},{"id":"ar-s019"}],
    }


class RehearsalTests(unittest.TestCase):
    def test_bilingual_event_survives_replay_into_two_separate_products(self):
        result = run_offline_rehearsal(fixture(), registry())
        self.assertEqual(result["journal"], result["replayed_journal"])
        en = result["products"]["english"]
        ar = result["products"]["arabic"]
        self.assertEqual(en["plan"]["selected"], 1)
        self.assertEqual(ar["plan"]["selected"], 1)
        self.assertEqual(en["plan"]["items"][0]["event_id"],
                         ar["plan"]["items"][0]["event_id"])
        self.assertEqual(en["layout"]["page_count"], 2)
        self.assertEqual(ar["layout"]["page_count"], 3)
        self.assertIn("Synthetic station", en["layout"]["pages"][0]["items"][0]["quote"])
        self.assertIn("محطة تجريبية", ar["layout"]["pages"][0]["items"][0]["quote"])

    def test_foreign_language_without_translation_is_explicitly_withheld(self):
        result = run_offline_rehearsal(fixture(), registry())
        for product in ("english","arabic"):
            p=result["products"][product]["plan"]
            self.assertEqual(p["held_reasons"]["no_native_language_source"],1)
            self.assertEqual(p["analysis_status"],"withheld_without_verified_analysis")
            self.assertNotIn("گزارش", str(result["products"][product]["layout"]))

    def test_no_network_db_llm_or_discord(self):
        result=run_offline_rehearsal(fixture(),registry())
        self.assertFalse(result["live_source_fetched"])
        self.assertFalse(result["live_model_called"])
        self.assertFalse(result["database_written"])
        self.assertFalse(result["discord_sent"])
        for product in ("english","arabic"):
            p=result["products"][product]
            self.assertFalse(p["network_send_attempted"])
            self.assertEqual(p["reservation"]["state"],"reserved")
            self.assertFalse(p["layout"]["delivery_authorized"])
        self.assertFalse(result["analytics_budget"]["permitted"])

    def test_english_and_arabic_channels_do_not_swap(self):
        r=run_offline_rehearsal(fixture(),registry())
        self.assertEqual(r["products"]["english"]["reservation"]["destination_key"],"discord_webhook")
        self.assertEqual(r["products"]["arabic"]["reservation"]["destination_key"],"discord_webhook_arabic")

    def test_fixture_using_actual_publisher_url_is_rejected(self):
        p=fixture()
        p["documents"][0]["url"]="https://www.bbc.co.uk/news/test"
        with self.assertRaisesRegex(ValueError,"prohibits_real_article_urls"):
            run_offline_rehearsal(p,registry())

    def test_non_synthetic_mode_refused(self):
        p=fixture()
        p["synthetic"]=False
        with self.assertRaisesRegex(ValueError,"requires_explicit_synthetic"):
            run_offline_rehearsal(p,registry())

    def test_unregistered_source_refused(self):
        p=fixture()
        p["documents"][0]["source_id"]="en-999"
        with self.assertRaisesRegex(ValueError,"source_not_in_versioned_registry"):
            run_offline_rehearsal(p,registry())

    def test_conflicting_event_annotation_fails(self):
        p=fixture()
        p["documents"][1]["priority"]=30
        with self.assertRaisesRegex(ValueError,"conflicting_explicit_event_annotations"):
            run_offline_rehearsal(p,registry())

    def test_unknown_input_fields_cannot_hide_publisher_assertion(self):
        p=fixture()
        p["documents"][0]["publisher_family_verified"]=True
        with self.assertRaisesRegex(ValueError,"unapproved_document_fields"):
            run_offline_rehearsal(p,registry())

    def test_unsupported_editorial_claim_never_becomes_fact(self):
        p=fixture()
        p["documents"][0]["original_text"]="ABC"
        with self.assertRaisesRegex(ValueError,"invalid_fixture_text_budget"):
            run_offline_rehearsal(p,registry())

    def test_registry_rights_cannot_be_manufactured(self):
        r=run_offline_rehearsal(fixture(),registry())
        self.assertEqual(r["real_publisher_rights"],"unreviewed")
        self.assertEqual(r["real_publisher_independence"],"unverified")
        self.assertEqual(r["products"]["arabic"]["plan"]["coverage_status"],"unverified_source_registry")


if __name__ == "__main__":
    unittest.main()
