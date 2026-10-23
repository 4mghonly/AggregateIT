"""B4 editorial contracts: all articles are synthetic and never publishable."""
import unittest
from v2_evidence import make_article, make_excerpt, make_claim, make_event
from v2_evidence_ledger import EvidenceLedger
from v2_editorial import plan_edition, AR_REGIONS

NOW = "2026-10-23T08:00:00+00:00"
SLOT = "2026-10-23T12:00:00+04:00"


def add(ledger, key, language, source, text, hours_ago=1):
    hour = 8-hours_ago
    stamp = "2026-10-23T%02d:00:00+00:00" % hour
    a = make_article(
        source_id=source, url="https://example.org/" + key,
        original_text=text, original_language=language,
        retrieved_at=stamp, published_at=stamp,
    )
    x = make_excerpt(a, 0, len(text))
    c = make_claim(statement="Synthetic report: " + text, excerpts=[x])
    e = make_event(key=key, claims=[c])
    ledger.observe(a)
    ledger.attach_excerpt(x)
    ledger.attach_claim(c)
    ledger.upsert_event(e)
    return e, x


def ann(event, region="gcc", country="AE", topic="security", priority=50):
    return dict(event_id=event["event_id"], region=region,
                subject_country=country, topic=topic, priority=priority)


class EditorialTests(unittest.TestCase):
    def setUp(self):
        self.ledger = EvidenceLedger()
        self.ar_uae, self.uae_x = add(
            self.ledger, "synthetic.uae.update", "ar", "ar-s001",
            "نشرت جهة تجريبية تحديثاً أمنياً")
        self.ar_yemen, self.yemen_x = add(
            self.ledger, "synthetic.yemen.update", "ar", "ar-s002",
            "ورد بيان تجريبي عن الحدود")
        self.en_market, self.en_x = add(
            self.ledger, "synthetic.market.update", "en", "en-001",
            "Synthetic market pulse was updated")
        self.fa, self.fa_x = add(
            self.ledger, "synthetic.iran.update", "fa", "ar-s003",
            "گزارش آزمایشی منتشر شد")

    def plan(self, product, anns, **kw):
        return plan_edition(
            ledger=self.ledger, annotations=anns, product=product,
            slot_id=SLOT, as_of=NOW, **kw)

    def test_arabic_uses_verbatim_quote_and_real_ledger_url(self):
        p = self.plan("arabic", [ann(self.ar_uae)])
        self.assertEqual(p["page_count"], 3)
        self.assertEqual(p["selected"], 1)
        item = p["items"][0]
        self.assertEqual(item["evidence"]["quote"], self.uae_x["literal"])
        self.assertEqual(item["evidence"]["literal_sha256"], self.uae_x["literal_sha256"])
        self.assertEqual(item["reporting_status"], "publisher_attributed_not_independently_verified")
        self.assertFalse(p["delivery_authorized"])

    def test_english_independently_excludes_arabic_and_includes_market(self):
        p = self.plan("english", [
            ann(self.ar_uae, topic="security"),
            ann(self.en_market, topic="markets")
        ])
        self.assertEqual(p["page_count"], 2)
        self.assertEqual(p["selected"], 1)
        self.assertEqual(p["items"][0]["topic"], "markets")
        self.assertEqual(p["held_reasons"]["no_native_language_source"], 1)

    def test_arabic_rejects_routine_market_topic(self):
        p = self.plan("arabic", [ann(self.en_market, topic="markets")])
        self.assertEqual(p["selected"], 0)
        self.assertEqual(p["held_reasons"]["topic_excluded_by_product"], 1)

    def test_no_unverified_persian_translation(self):
        p = self.plan("arabic", [ann(self.fa, region="iran", country="IR")])
        self.assertEqual(p["selected"], 0)
        self.assertEqual(p["held_reasons"]["no_native_language_source"], 1)
        self.assertIn("iran", p["missing_target_regions"])

    def test_uae_first_then_distinct_regions(self):
        anns = [
            ann(self.ar_yemen, region="yemen", country="YE", priority=100),
            ann(self.ar_uae, priority=1),
        ]
        p = self.plan("arabic", anns)
        self.assertEqual([x["event_id"] for x in p["items"]],
                         [self.ar_uae["event_id"], self.ar_yemen["event_id"]])

    def test_no_automatic_event_merging(self):
        p = self.plan("arabic", [ann(self.ar_uae), ann(self.ar_uae)])
        self.assertEqual(p["selected"], 1)
        self.assertEqual(p["held_reasons"]["duplicate_event_annotation"], 1)

    def test_missing_regions_are_explicit(self):
        p = self.plan("arabic", [])
        self.assertEqual(len(p["missing_target_regions"]), len(AR_REGIONS))
        self.assertEqual(p["coverage_status"], "unverified_source_registry")

    def test_previous_edition_delta_is_version_id_based(self):
        a = ann(self.ar_uae)
        self.assertEqual(self.plan("arabic", [a])["items"][0]["change"], "unknown_no_baseline")
        self.assertEqual(self.plan("arabic", [a], previous_versions={})["items"][0]["change"], "new")
        p = self.plan("arabic", [a], previous_versions={
            self.ar_uae["event_id"]: self.ar_uae["version_id"]})
        self.assertEqual(p["items"][0]["change"], "unchanged")

    def test_editorial_metadata_not_injected_as_headline(self):
        entry = ann(self.ar_uae)
        entry["headline"] = "Fake unsupported announcement"
        p = self.plan("arabic", [entry])
        self.assertEqual(p["selected"], 0)
        self.assertIn("invalid_editorial_annotation", p["held_reasons"])

    def test_stale_event_explicitly_held(self):
        old, _ = add(self.ledger, "synthetic.old.story", "ar",
                     "ar-s005", "تقرير قديم للاختبار", hours_ago=6)
        p = self.plan("arabic", [ann(old)], max_age_hours=2)
        self.assertEqual(p["selected"], 0)
        self.assertEqual(p["held_reasons"]["stale_or_future_source"], 1)

    def test_unknown_event_held(self):
        a = ann(self.ar_uae)
        a["event_id"] = "evt_" + "f"*24
        p = self.plan("arabic", [a])
        self.assertEqual(p["held_reasons"]["event_not_in_evidence_ledger"], 1)

    def test_analyst_inference_cannot_be_a_news_item(self):
        a = make_article(source_id="ar-s004", url="https://example.org/inference",
            original_text="نص استدلال افتراضي", original_language="ar",
            retrieved_at=NOW, published_at=NOW)
        x = make_excerpt(a,0,len(a["original_text"]))
        c = make_claim(statement="unsupported extrapolation",excerpts=[x],kind="analyst_inference")
        e = make_event(key="synthetic.inference",claims=[c])
        self.ledger.observe(a);self.ledger.attach_excerpt(x);self.ledger.attach_claim(c);self.ledger.upsert_event(e)
        p = self.plan("arabic",[ann(e)])
        self.assertEqual(p["selected"],0)

    def test_invalid_product_or_budget_fails_closed(self):
        with self.assertRaises(ValueError):
            self.plan("spanish", [])
        with self.assertRaises(ValueError):
            self.plan("arabic", [], max_items=0)

    def test_page_overflow_logged_and_no_duplicate(self):
        p = self.plan("arabic", [
            ann(self.ar_uae, priority=1),
            ann(self.ar_yemen, region="yemen",country="YE", priority=90)
        ], max_items=1)
        self.assertEqual(p["selected"], 1)
        self.assertEqual(p["held_reasons"]["eligible_over_page_budget"], 1)

    def test_no_claim_of_publisher_independence(self):
        p = self.plan("arabic", [ann(self.ar_uae)])
        self.assertEqual(p["items"][0]["publisher_independence"], "unverified")


if __name__ == "__main__":
    unittest.main()
