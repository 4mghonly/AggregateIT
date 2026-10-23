"""B4 typo/mislabelling guard with explicit limits on language inference."""
import unittest

from v2_evidence import make_article, make_excerpt, make_claim, make_event
from v2_evidence_ledger import EvidenceLedger
from v2_editorial import plan_edition
from v2_script_guard import script_consistent


STAMP = "2026-10-23T08:00:00+00:00"


def admission(language, text, product):
    article = make_article(
        source_id="ar-s001" if product == "arabic" else "en-001",
        url="https://fixture.invalid/script-guard", original_text=text,
        original_language=language, retrieved_at=STAMP, published_at=STAMP)
    excerpt = make_excerpt(article, 0, len(text))
    claim = make_claim(statement="Synthetic attributed: " + text, excerpts=[excerpt])
    event = make_event(key="synthetic.script-guard", claims=[claim])
    ledger = EvidenceLedger()
    ledger.observe(article)
    ledger.attach_excerpt(excerpt)
    ledger.attach_claim(claim)
    ledger.upsert_event(event)
    return plan_edition(
        ledger=ledger,
        annotations=[{"event_id": event["event_id"], "region": "gcc",
                      "subject_country": "AE", "topic": "security" if product == "arabic" else "geopolitics",
                      "priority": 70}],
        product=product, slot_id="2026-10-23T12:00:00+04:00", as_of=STAMP)


class ScriptGuardTests(unittest.TestCase):
    def test_native_script_examples(self):
        self.assertTrue(script_consistent("The fictional agency issued a test statement.", "en"))
        self.assertTrue(script_consistent("أعلنت المؤسسة التجريبية بياناً جديداً.", "ar-AE"))
        self.assertTrue(script_consistent("أعلنت هيئة التدريب ABC عن مناورات تجريبية.", "ar"))

    def test_obvious_wrong_script_is_refused_in_editorial_plan(self):
        arabic = admission("ar", "This fictional English paragraph is not Arabic.", "arabic")
        self.assertEqual(arabic["selected"], 0)
        self.assertEqual(arabic["held_reasons"], {"source_script_mismatch": 1})
        english = admission("en", "هذا بيان عربي خيالي للاختبار.", "english")
        self.assertEqual(english["selected"], 0)
        self.assertEqual(english["held_reasons"], {"source_script_mismatch": 1})

    def test_valid_script_remains_admissible_but_not_verified(self):
        p = admission("ar", "ورد بيان تجريبي حول الأمن الإقليمي.", "arabic")
        self.assertEqual(p["selected"], 1)
        self.assertEqual(p["items"][0]["publisher_independence"], "unverified")
        self.assertFalse(p["delivery_authorized"])

    def test_ambiguous_and_too_short_excerpts_do_not_claim_language(self):
        self.assertFalse(script_consistent("ABC", "en"))
        self.assertFalse(script_consistent("12345!", "ar"))
        self.assertFalse(script_consistent("hello مرحبا", "ar"))
        self.assertFalse(script_consistent("hello مرحبا", "en"))
        self.assertFalse(script_consistent(None, "en"))

    def test_arabic_script_cannot_prove_arabic_language(self):
        # Deliberate limit: Persian also uses Arabic script. Passing is not
        # proof and must NEVER be counted as a verified Arabic source.
        self.assertTrue(script_consistent("گزارش آزمایشی درباره وضعیت منطقه منتشر شد.", "ar"))
        self.assertFalse(script_consistent("گزارش آزمایشی درباره وضعیت منطقه منتشر شد.", "fa"))


if __name__ == "__main__":
    unittest.main()
