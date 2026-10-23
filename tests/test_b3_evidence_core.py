"""Deterministic B3 evidence contracts: only synthetic content, no model or network."""
import unittest
import copy

from v2_evidence import (
    canonical_article_url, make_article, make_excerpt, make_claim, make_event,
    event_delta, make_translation,
)

STAMP = "2026-10-23T06:00:00+00:00"
URL = "https://example.org/news/42?utm_source=feed&edition=ar#intro"


def article(source_id="ar-s001", text="أعلنت الهيئة تحديث البيان.", **other):
    return make_article(
        source_id=source_id,
        url=other.pop("url", URL), original_text=text,
        original_language=other.pop("original_language", "ar"),
        retrieved_at=other.pop("retrieved_at", STAMP),
        published_at=other.pop("published_at", STAMP), **other,
    )


def claim_for(a, statement="الهيئة نشرت بياناً"):
    return make_claim(statement=statement, excerpts=[make_excerpt(a, 0, len(a["original_text"]))])


class EvidenceTests(unittest.TestCase):
    def test_canonical_removes_only_known_trackers_and_fragments(self):
        self.assertEqual(canonical_article_url(URL), "https://example.org/news/42?edition=ar")
        self.assertEqual(canonical_article_url("HTTPS://Example.Org/n/?x=2&x=1&gclid=a"),
                         "https://example.org/n?x=2&x=1")

    def test_canonical_rejects_unsupported_scheme_credentials_and_localhost(self):
        for url in ("file:///etc/passwd", "https://u:p@example.org/", "https://localhost/x", "x", ""):
            with self.subTest(url=url), self.assertRaises(ValueError):
                canonical_article_url(url)

    def test_article_id_stable_across_capture_and_original_revision(self):
        a = article()
        later = article(retrieved_at="2026-10-23T07:00:00+00:00")
        changed = article(text="أعلنت الهيئة تحديثين.")
        self.assertEqual(a["article_id"], later["article_id"])
        self.assertEqual(a["revision_id"], later["revision_id"])
        self.assertNotEqual(a["observation_id"], later["observation_id"])
        self.assertNotEqual(a["revision_id"], changed["revision_id"])

    def test_source_observations_distinct_even_when_canonical_article_shared(self):
        a = article("ar-s001")
        b = article("en-001")
        self.assertEqual(a["article_id"], b["article_id"])
        self.assertNotEqual(a["observation_id"], b["observation_id"])
        self.assertNotEqual(make_excerpt(a, 0, 2)["excerpt_id"], make_excerpt(b, 0, 2)["excerpt_id"])
        self.assertNotEqual(a["source_id"], b["source_id"])

    def test_original_arabic_codepoint_spans_are_verbatim(self):
        a = article(text="🚨 خبر جديد")
        e = make_excerpt(a, 2, 5)
        self.assertEqual(e["literal"], "خبر")
        self.assertEqual((e["start_cp"], e["end_cp"]), (2, 5))
        self.assertEqual(e["original_language"], "ar")
        self.assertEqual(a["original_text"], "🚨 خبر جديد")

    def test_invalid_excerpts_rejected(self):
        a = article()
        for start, end in ((2, 2), (-1, 2), (0, 30000), (True, 2)):
            with self.subTest(span=(start, end)), self.assertRaises(ValueError):
                make_excerpt(a, start, end)

    def test_article_integrity_prevents_tampered_original(self):
        a = article()
        forged = copy.deepcopy(a)
        forged["original_text"] += " forged"
        with self.assertRaisesRegex(ValueError, "invalid_article_integrity"):
            make_excerpt(forged, 0, 1)

    def test_excerpt_integrity_prevents_tampered_literal(self):
        a = article()
        excerpt = make_excerpt(a, 0, 5)
        excerpt["literal"] = "altered"
        with self.assertRaisesRegex(ValueError, "excerpt_integrity_failed"):
            make_claim(statement="reported", excerpts=[excerpt])

    def test_claim_integrity_prevents_tampered_statement_in_event(self):
        a = article()
        c = claim_for(a)
        c["statement"] = "new false statement"
        with self.assertRaisesRegex(ValueError, "claim_integrity_failed"):
            make_event(key="test.20261023.incident42", claims=[c])

    def test_source_bound_claim_cannot_have_empty_or_forged_excerpt(self):
        a = article()
        with self.assertRaisesRegex(ValueError, "claim_requires"):
            make_claim(statement="x", excerpts=[])
        with self.assertRaisesRegex(ValueError, "invalid_excerpt_reference"):
            make_claim(statement="x", excerpts=[{"excerpt_id": "fake"}])
        with self.assertRaisesRegex(ValueError, "claim_kind"):
            make_claim(statement="x", excerpts=[make_excerpt(a, 0, 1)], kind="verified_fact")

    def test_claim_id_invariant_to_excerpt_order(self):
        a = article()
        x, y = make_excerpt(a, 0, 5), make_excerpt(a, 6, 10)
        c1 = make_claim(statement="Attribution", excerpts=[x, y])
        c2 = make_claim(statement="Attribution", excerpts=[y, x])
        self.assertEqual(c1["claim_id"], c2["claim_id"])
        self.assertEqual(c1["release_status"], "attributed_only")

    def test_analyst_inference_not_reported_fact(self):
        a = article()
        c = make_claim(statement="Inference", excerpts=[make_excerpt(a, 0, 1)], kind="analyst_inference")
        self.assertEqual(c["release_status"], "not_a_reported_fact")

    def test_event_identity_explicit_and_stable_on_claim_addition(self):
        a = article()
        c1, c2 = claim_for(a, "A"), claim_for(a, "B")
        v1 = make_event(key="test.20261023.incident42", claims=[c1])
        v2 = make_event(key="test.20261023.incident42", claims=[c2, c1])
        self.assertEqual(v1["event_id"], v2["event_id"])
        self.assertNotEqual(v1["version_id"], v2["version_id"])
        self.assertEqual(event_delta(v1, v2), "changed")

    def test_event_key_absence_forbids_speculative_merge(self):
        a = article()
        with self.assertRaisesRegex(ValueError, "explicit_key"):
            make_event(key="", claims=[claim_for(a)])

    def test_closure_requires_explicit_cited_claim(self):
        c = claim_for(article())
        with self.assertRaisesRegex(ValueError, "closure_requires"):
            make_event(key="test.20261023.incident42", claims=[c], status="closed")
        open_ev = make_event(key="test.20261023.incident42", claims=[c])
        closed_ev = make_event(key="test.20261023.incident42", claims=[c], status="closed",
                               closure_claim_id=c["claim_id"])
        self.assertEqual(event_delta(open_ev, closed_ev), "explicitly_closed")

    def test_unchanged_and_new_event_state(self):
        e = make_event(key="test.20261023.incident42", claims=[claim_for(article())])
        self.assertEqual(event_delta(None, e), "new")
        self.assertEqual(event_delta(e, e), "unchanged")
        other = make_event(key="test.20261023.incident43", claims=[claim_for(article())])
        with self.assertRaises(ValueError):
            event_delta(e, other)

    def test_translation_candidate_preserves_original_and_is_unverified(self):
        a = article()
        original = a["original_text"]
        t = make_translation(article=a, target_language="en",
                             candidate_text="A statement was updated.", engine_id="synthetic-test")
        self.assertEqual(a["original_text"], original)
        self.assertEqual(t["source_revision_id"], a["revision_id"])
        self.assertEqual(t["verification"], "unverified_candidate")
        self.assertEqual(t["source_language"], "ar")

    def test_requires_aware_capture_time_and_valid_source_identity(self):
        with self.assertRaises(ValueError):
            article(retrieved_at="2026-10-23T06:00:00")
        with self.assertRaises(ValueError):
            article("invented_source")

    def test_event_does_not_claim_independent_publishers(self):
        a = article()
        e = make_event(key="test.20261023.incident42", claims=[claim_for(a)])
        self.assertEqual(e["publisher_independence"], "unverified")


if __name__ == "__main__":
    unittest.main()
