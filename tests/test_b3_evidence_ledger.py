"""B3b in-memory ledger tests with synthetic bilingual observations only."""
import copy
import unittest

from v2_evidence import make_article, make_excerpt, make_claim, make_event
from v2_evidence_ledger import EvidenceLedger

STAMP = "2026-10-23T06:00:00+00:00"


def new_article(source="ar-s001", content="خبر جديد", url="https://example.org/a"):
    return make_article(
        source_id=source, url=url, original_text=content,
        original_language="ar" if source.startswith("ar-") else "en",
        retrieved_at=STAMP, published_at=STAMP,
    )


def anchored(ledger, a, statement="Source reported something"):
    ledger.observe(a)
    x = make_excerpt(a, 0, len(a["original_text"]))
    ledger.attach_excerpt(x)
    c = make_claim(statement=statement, excerpts=[x])
    ledger.attach_claim(c)
    return x, c


class LedgerTests(unittest.TestCase):
    def test_append_observation_idempotent(self):
        ledger = EvidenceLedger()
        a = new_article()
        self.assertTrue(ledger.observe(a))
        self.assertFalse(ledger.observe(a))
        self.assertEqual(ledger.counters()["observations"], 1)

    def test_two_product_observations_share_article_not_source_provenance(self):
        ledger = EvidenceLedger()
        a = new_article("ar-s001")
        b = new_article("en-001")
        ledger.observe(a)
        ledger.observe(b)
        self.assertEqual(ledger.counters()["unique_articles"], 1)
        self.assertEqual(ledger.counters()["duplicate_article_observations"], 1)
        self.assertNotEqual(make_excerpt(a, 0, 2)["excerpt_id"], make_excerpt(b, 0, 2)["excerpt_id"])
        self.assertEqual(ledger.counters()["publisher_independence"], "not_verified")

    def test_explicit_observation_budget(self):
        ledger = EvidenceLedger(max_observations=1)
        ledger.observe(new_article())
        with self.assertRaisesRegex(ValueError, "observation_ceiling"):
            ledger.observe(new_article("en-001"))

    def test_tampered_observation_refused(self):
        ledger = EvidenceLedger()
        a = new_article()
        a["observation_id"] = "obs_" + "f"*24
        with self.assertRaisesRegex(ValueError, "invalid_article_integrity"):
            ledger.observe(a)

    def test_exact_stored_source_required_for_excerpt(self):
        ledger = EvidenceLedger()
        a = new_article()
        x = make_excerpt(a, 0, 2)
        with self.assertRaisesRegex(ValueError, "without_stored_revision"):
            ledger.attach_excerpt(x)
        ledger.observe(a)
        self.assertTrue(ledger.attach_excerpt(x))
        self.assertFalse(ledger.attach_excerpt(x))

    def test_tampered_excerpt_refused_against_original(self):
        ledger = EvidenceLedger()
        a = new_article()
        ledger.observe(a)
        x = make_excerpt(a, 0, 2)
        x["literal"] = "false"
        with self.assertRaisesRegex(ValueError, "does_not_match"):
            ledger.attach_excerpt(x)

    def test_claim_cannot_reference_unstored_excerpt(self):
        ledger = EvidenceLedger()
        a = new_article()
        x = make_excerpt(a, 0, 2)
        c = make_claim(statement="source says X", excerpts=[x])
        with self.assertRaisesRegex(ValueError, "missing_excerpt"):
            ledger.attach_claim(c)
        ledger.observe(a)
        ledger.attach_excerpt(x)
        self.assertTrue(ledger.attach_claim(c))
        self.assertFalse(ledger.attach_claim(c))

    def test_claim_integrity_checks_statement_and_source_revision(self):
        ledger = EvidenceLedger()
        a = new_article()
        _, c = anchored(ledger, a)
        altered = copy.deepcopy(c)
        altered["statement"] = "invented"
        with self.assertRaisesRegex(ValueError, "claim_integrity"):
            ledger.attach_claim(altered)

    def test_event_requires_claims_present_and_no_automatic_merges(self):
        ledger = EvidenceLedger()
        a = new_article()
        x = make_excerpt(a, 0, 2)
        c = make_claim(statement="allegation", excerpts=[x])
        ev = make_event(key="local.event42", claims=[c])
        with self.assertRaisesRegex(ValueError, "missing_claim"):
            ledger.upsert_event(ev)
        anchored(ledger, a, "allegation")
        # The claim above used the full excerpt; attach exact event claim separately.
        ledger.attach_excerpt(x)
        ledger.attach_claim(c)
        self.assertEqual(ledger.upsert_event(ev), "new")

    def test_event_revision_history_and_explicit_close(self):
        ledger = EvidenceLedger()
        a = new_article()
        _, c1 = anchored(ledger, a, "A")
        _, c2 = anchored(ledger, a, "B")
        e1 = make_event(key="local.event42", claims=[c1])
        e2 = make_event(key="local.event42", claims=[c1, c2])
        e3 = make_event(key="local.event42", claims=[c1, c2], status="closed", closure_claim_id=c2["claim_id"])
        self.assertEqual(ledger.upsert_event(e1), "new")
        self.assertEqual(ledger.upsert_event(e1), "unchanged")
        self.assertEqual(ledger.upsert_event(e2), "changed")
        self.assertEqual(ledger.upsert_event(e3), "explicitly_closed")
        self.assertEqual(ledger.counters()["event_versions"], 3)

    def test_explicit_contradiction_requires_event_attached_claims(self):
        ledger = EvidenceLedger()
        a = new_article()
        _, c1 = anchored(ledger, a, "A")
        _, c2 = anchored(ledger, a, "B")
        ev = make_event(key="local.event42", claims=[c1, c2])
        ledger.upsert_event(ev)
        self.assertTrue(ledger.relate(
            event_id=ev["event_id"], kind="contradiction",
            first_claim_id=c1["claim_id"], second_claim_id=c2["claim_id"],
            rationale="Synthetic conflicting assertions",
        ))
        self.assertFalse(ledger.relate(
            event_id=ev["event_id"], kind="contradiction",
            first_claim_id=c1["claim_id"], second_claim_id=c2["claim_id"],
            rationale="Synthetic conflicting assertions",
        ))
        self.assertEqual(ledger.counters()["explicit_relations"], 1)

    def test_cannot_infer_contradiction_without_explicit_relation(self):
        ledger = EvidenceLedger()
        a = new_article()
        _, c1 = anchored(ledger, a, "A")
        _, c2 = anchored(ledger, a, "B")
        ev = make_event(key="local.event42", claims=[c1, c2])
        ledger.upsert_event(ev)
        self.assertEqual(ledger.counters()["explicit_relations"], 0)

    def test_relation_rejects_unlinked_claim_or_unapproved_kind(self):
        ledger = EvidenceLedger()
        a = new_article()
        _, c1 = anchored(ledger, a, "A")
        _, c2 = anchored(ledger, a, "B")
        ev = make_event(key="local.event42", claims=[c1])
        ledger.upsert_event(ev)
        with self.assertRaisesRegex(ValueError, "not_in_event"):
            ledger.relate(event_id=ev["event_id"], kind="correction",
                          first_claim_id=c1["claim_id"], second_claim_id=c2["claim_id"], rationale="replace")
        with self.assertRaisesRegex(ValueError, "invalid_relation_kind"):
            ledger.relate(event_id=ev["event_id"], kind="random",
                          first_claim_id=c1["claim_id"], second_claim_id=c2["claim_id"], rationale="replace")

    def test_counters_expose_no_raw_evidence(self):
        ledger = EvidenceLedger()
        a = new_article(content="PRIVATE SYNTHETIC TEST")
        anchored(ledger, a)
        summary = str(ledger.counters())
        self.assertNotIn("PRIVATE", summary)
        self.assertNotIn("https://", summary)

    def test_new_capture_same_revision_retained_as_new_observation(self):
        ledger = EvidenceLedger()
        a = new_article()
        b = dict(a)
        b["retrieved_at"] = "2026-10-23T12:00:00+00:00"
        # Caller must use the builder for the new observation identity.
        b = make_article(source_id=a["source_id"], url=a["canonical_url"],
                         original_text=a["original_text"], original_language="ar",
                         retrieved_at="2026-10-23T12:00:00+00:00", published_at=STAMP)
        ledger.observe(a)
        ledger.observe(b)
        self.assertEqual(ledger.counters()["observations"], 2)
        self.assertEqual(ledger.counters()["unique_articles"], 1)


if __name__ == "__main__":
    unittest.main()
