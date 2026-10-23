"""B5 contract-only layout tests; NO image/Discord generation."""
import copy
import unittest

from v2_evidence import make_article, make_excerpt, make_claim, make_event
from v2_evidence_ledger import EvidenceLedger
from v2_editorial import plan_edition
from v2_layout import layout_plan

TIME = "2026-10-23T08:00:00+00:00"
SLOT = "2026-10-23T12:00:00+04:00"


def one(ledger, key, language, source, topic, region, country, text):
    a = make_article(source_id=source, url="https://example.org/"+key,
                     original_text=text, original_language=language,
                     retrieved_at=TIME, published_at=TIME)
    x = make_excerpt(a, 0, len(text))
    c = make_claim(statement="synthetic only", excerpts=[x])
    e = make_event(key=key, claims=[c])
    ledger.observe(a); ledger.attach_excerpt(x)
    ledger.attach_claim(c); ledger.upsert_event(e)
    ann = {"event_id": e["event_id"], "region": region,
           "subject_country": country, "topic": topic, "priority": 50}
    return e, ann


def edition(ledger, product, anns):
    return plan_edition(ledger=ledger, annotations=anns, product=product,
                        slot_id=SLOT, as_of=TIME)


class LayoutTests(unittest.TestCase):
    def setUp(self):
        self.ledger = EvidenceLedger()

    def test_fixed_three_arabic_frames_and_region_geography(self):
        _, a1 = one(self.ledger, "synthetic.uae.security", "ar", "ar-s001",
                    "security", "gcc", "AE", "بيان أمني افتراضي للإمارات")
        _, a2 = one(self.ledger, "synthetic.iran.diplomacy", "ar", "ar-s002",
                    "diplomacy", "iran", "IR", "إعلان تجريبي دبلوماسي")
        _, a3 = one(self.ledger, "synthetic.sudan.safety", "ar", "ar-s003",
                    "security", "sudan", "SD", "بيان افتراضي للسلامة")
        deck = layout_plan(edition(self.ledger, "arabic", [a1,a2,a3]), self.ledger)
        self.assertEqual(deck["page_count"], 3)
        self.assertEqual([len(p["items"]) for p in deck["pages"]], [1,1,1])
        self.assertEqual(deck["style"]["direction"], "rtl")
        self.assertFalse(deck["delivery_authorized"])

    def test_english_finance_and_geo_occupy_separate_pages(self):
        _, a1 = one(self.ledger, "synthetic.trade.disruption", "en", "en-001",
                    "geopolitics", "gcc", "AE", "Synthetic geopolitical update")
        _, a2 = one(self.ledger, "synthetic.stock.market", "en", "en-002",
                    "markets", "gcc", "AE", "Synthetic market indicator")
        deck = layout_plan(edition(self.ledger, "english", [a1,a2]), self.ledger)
        self.assertEqual(deck["page_count"], 2)
        self.assertEqual([len(p["items"]) for p in deck["pages"]], [1,1])

    def test_tampered_quote_is_rejected(self):
        _, a = one(self.ledger, "synthetic.quote", "ar", "ar-s001",
                   "security", "gcc", "AE", "المصدر ينشر نصاً تجريبياً")
        plan = edition(self.ledger, "arabic", [a])
        plan["items"][0]["evidence"]["quote"] = "افتراء"
        with self.assertRaisesRegex(ValueError, "quote_integrity_mismatch"):
            layout_plan(plan, self.ledger)

    def test_tampered_source_url_is_rejected(self):
        _, a = one(self.ledger, "synthetic.url", "ar", "ar-s001",
                   "security", "gcc", "AE", "بيان آخر للتجربة")
        plan = edition(self.ledger, "arabic", [a])
        plan["items"][0]["evidence"]["source_url"] = "https://evil.example/"
        with self.assertRaisesRegex(ValueError, "source_url_or_identity"):
            layout_plan(plan, self.ledger)

    def test_overflow_is_explicit_and_text_not_cropped(self):
        anns = []
        for i in range(6):
            region, country = ("gcc", "AE") if i < 4 else (("oman", "OM") if i == 4 else ("gcc", "SA"))
            _, a = one(self.ledger, "synthetic.gulf.%d"%i, "ar", "ar-s%03d"%(i+1),
                       "security", region, country, "بيان تجريبي دون اختصار رقم %d"%i)
            anns.append(a)
        plan = edition(self.ledger, "arabic", anns)
        deck = layout_plan(plan, self.ledger)
        self.assertEqual(len(deck["pages"][0]["items"]), 4)
        self.assertEqual(len(deck["omissions"]), 2)
        self.assertTrue(all(x["reason"] == "page_card_limit" for x in deck["omissions"]))

    def test_long_quote_overflow_never_truncated(self):
        _, a = one(self.ledger, "synthetic.long", "en", "en-001",
                   "markets", "gcc", "AE", "x"*230)
        plan = edition(self.ledger, "english", [a])
        deck = layout_plan(plan, self.ledger)
        self.assertEqual(deck["pages"][1]["items"][0]["quote"], "x"*230)

    def test_non_isolated_plan_refused(self):
        _, a = one(self.ledger, "synthetic.guard", "ar", "ar-s001",
                   "security", "gcc", "AE", "حدث تجريبي")
        plan = edition(self.ledger, "arabic", [a])
        plan["delivery_authorized"] = True
        with self.assertRaisesRegex(ValueError, "non_isolated"):
            layout_plan(plan, self.ledger)

    def test_no_fake_scaled_image_qa(self):
        deck = layout_plan(edition(self.ledger, "arabic", []), self.ledger)
        self.assertEqual(deck["scaled_image_qa"], "not_run")
        self.assertEqual(deck["rendered_items"], 0)


if __name__ == "__main__":
    unittest.main()
