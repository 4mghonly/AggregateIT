"""B3 journal regression: synthetic bytes and in-memory streams only."""
import io
import json
import unittest

from v2_evidence import make_article, make_excerpt, make_claim, make_event
from v2_evidence_journal import EvidenceJournal

STAMP = "2026-10-23T06:00:00+00:00"


def fixtures():
    article = make_article(
        source_id="ar-s001", url="https://example.org/synthetic?id=5",
        original_text="🚨 بيان اختبار فقط", original_language="ar",
        retrieved_at=STAMP, published_at=STAMP,
    )
    excerpt = make_excerpt(article, 2, len(article["original_text"]))
    claim = make_claim(statement="صدر بيان تجريبي", excerpts=[excerpt])
    event = make_event(key="synthetic.uae.one", claims=[claim])
    return article, excerpt, claim, event


def filled():
    stream = io.StringIO()
    journal = EvidenceJournal()
    a, x, c, e = fixtures()
    for kind, item in (("observe", a), ("excerpt", x), ("claim", c), ("event", e)):
        journal.append(stream, kind, item, durable=False)
    return stream, journal


class BrokenStream(io.StringIO):
    def write(self, text):
        super().write(text[:9])
        return 9


class JournalTests(unittest.TestCase):
    def test_replay_matches_source_provenance_and_receipt(self):
        stream, original = filled()
        restored = EvidenceJournal.replay(stream.getvalue(), expected_head=original.head)
        self.assertEqual(restored.receipt(), original.receipt())
        self.assertEqual(restored.ledger._claims, original.ledger._claims)

    def test_append_on_verified_replay(self):
        stream, original = filled()
        restored = EvidenceJournal.replay(stream.getvalue(), expected_head=original.head)
        _, _, c, _ = fixtures()
        closed = make_event(key="synthetic.uae.one", claims=[c],
                            status="closed", closure_claim_id=c["claim_id"])
        self.assertEqual(restored.append(stream, "event", closed, durable=False), "explicitly_closed")
        again = EvidenceJournal.replay(stream.getvalue())
        self.assertEqual(again.ledger.counters()["event_versions"], 2)

    def test_reject_tampered_bytes(self):
        stream, _ = filled()
        changed = stream.getvalue().replace("بيان اختبار", "خبر اختبار")
        with self.assertRaisesRegex(ValueError, "journal_hash"):
            EvidenceJournal.replay(changed)

    def test_reject_reordered_frames(self):
        stream, _ = filled()
        rows = stream.getvalue().splitlines(keepends=True)
        with self.assertRaises(ValueError):
            EvidenceJournal.replay("".join([rows[1], rows[0], *rows[2:]]))

    def test_reject_truncated_partial_record(self):
        stream, _ = filled()
        with self.assertRaisesRegex(ValueError, "journal_truncated_tail"):
            EvidenceJournal.replay(stream.getvalue()[:-6])

    def test_external_receipt_catches_complete_tail_loss(self):
        stream, original = filled()
        rows = stream.getvalue().splitlines(keepends=True)
        with self.assertRaisesRegex(ValueError, "receipt_mismatch"):
            EvidenceJournal.replay("".join(rows[:-1]), expected_head=original.head)

    def test_reject_extra_keys_or_noncanonical_json(self):
        stream, _ = filled()
        frame = json.loads(stream.getvalue().splitlines()[0])
        frame["extra"] = "unexpected"
        with self.assertRaises(ValueError):
            EvidenceJournal.replay(json.dumps(frame) + "\n")

    def test_durable_fsync_required_without_fileno(self):
        stream = io.StringIO()
        journal = EvidenceJournal()
        with self.assertRaises(Exception):
            journal.append(stream, "observe", fixtures()[0])
        self.assertTrue(journal.poisoned)
        with self.assertRaisesRegex(RuntimeError, "requires_recovery"):
            journal.append(stream, "observe", fixtures()[0], durable=False)

    def test_short_write_poison_and_no_live_mutation(self):
        journal = EvidenceJournal()
        with self.assertRaisesRegex(OSError, "short_write"):
            journal.append(BrokenStream(), "observe", fixtures()[0], durable=False)
        self.assertEqual(journal.ledger.counters()["observations"], 0)
        self.assertTrue(journal.poisoned)

    def test_refuse_invalid_reference_without_journal_write(self):
        stream = io.StringIO()
        journal = EvidenceJournal()
        with self.assertRaises(ValueError):
            journal.append(stream, "claim", fixtures()[2], durable=False)
        self.assertEqual(stream.getvalue(), "")
        self.assertFalse(journal.poisoned)

    def test_idempotent_observation_replay(self):
        stream, journal = filled()
        before = journal.ledger.counters()
        self.assertFalse(journal.append(stream, "observe", fixtures()[0], durable=False))
        restored = EvidenceJournal.replay(stream.getvalue())
        self.assertEqual(restored.ledger.counters(), before)

    def test_unknown_command_refused(self):
        with self.assertRaisesRegex(ValueError, "unsupported_journal_command"):
            EvidenceJournal().append(io.StringIO(), "purge", {}, durable=False)

    def test_non_string_input_refused(self):
        with self.assertRaisesRegex(ValueError, "invalid_journal_size"):
            EvidenceJournal.replay(b"not text")

    def test_no_false_publisher_verification(self):
        stream, original = filled()
        view = EvidenceJournal.replay(stream.getvalue()).receipt()
        self.assertEqual(view["counters"]["publisher_independence"], "not_verified")
        self.assertEqual(original.ledger.counters()["events"], 1)


if __name__ == "__main__":
    unittest.main()
