"""B3 file-backed crash semantics using only disposable synthetic journals.

No network, production data, database, model or delivery calls. The store owner
must separately persist receipts and provide exclusive-writer coordination.
"""
import os
import tempfile
import unittest

from v2_evidence import make_article, make_excerpt, make_claim, make_event
from v2_evidence_journal import EvidenceJournal

STAMP = "2026-10-23T08:00:00+00:00"


def fixture():
    article = make_article(
        source_id="ar-s056",
        url="https://example.org/synthetic-file-proof",
        original_text="بيان عربي تجريبي محفوظ",
        original_language="ar",
        retrieved_at=STAMP,
        published_at=STAMP,
    )
    excerpt = make_excerpt(article, 0, len(article["original_text"]))
    claim = make_claim(statement="نشر مصدر تجريبي بياناً", excerpts=[excerpt])
    event = make_event(key="synthetic.file.recovery", claims=[claim])
    return (("observe", article), ("excerpt", excerpt),
            ("claim", claim), ("event", event))


def durable_file(root):
    path = os.path.join(root, "journal.jsonl")
    journal = EvidenceJournal()
    with open(path, "a+", encoding="utf-8", newline="") as sink:
        for kind, item in fixture():
            journal.append(sink, kind, item, durable=True)
    with open(path, encoding="utf-8") as src:
        contents = src.read()
    return path, journal, contents


class FileBackedRecoveryTests(unittest.TestCase):
    def test_fsync_roundtrip_and_external_receipt(self):
        with tempfile.TemporaryDirectory(prefix="aggregateit-b3-", dir="/tmp") as root:
            path, journal, contents = durable_file(root)
            self.assertGreater(os.stat(path).st_size, 0)
            recovered = EvidenceJournal.replay(contents, expected_head=journal.head)
            self.assertEqual(recovered.receipt(), journal.receipt())
            self.assertEqual(recovered.ledger.counters()["events"], 1)

    def test_torn_record_rejected_without_automatic_truncation(self):
        with tempfile.TemporaryDirectory(prefix="aggregateit-b3-", dir="/tmp") as root:
            _, journal, contents = durable_file(root)
            truncated = contents + '{"v":1'
            with self.assertRaisesRegex(ValueError, "truncated_tail"):
                EvidenceJournal.replay(truncated, expected_head=journal.head)
            # Recovery is deliberately fail-closed; only the store owner can repair.
            self.assertEqual(EvidenceJournal.replay(contents).head, journal.head)

    def test_complete_tail_loss_rejected_by_separate_receipt(self):
        with tempfile.TemporaryDirectory(prefix="aggregateit-b3-", dir="/tmp") as root:
            _, journal, contents = durable_file(root)
            prefix = "".join(contents.splitlines(keepends=True)[:-1])
            self.assertEqual(EvidenceJournal.replay(prefix).seq, journal.seq - 1)
            with self.assertRaisesRegex(ValueError, "receipt_mismatch"):
                EvidenceJournal.replay(prefix, expected_head=journal.head)

    def test_recovered_log_can_append_correction_durably(self):
        with tempfile.TemporaryDirectory(prefix="aggregateit-b3-", dir="/tmp") as root:
            path, journal, contents = durable_file(root)
            recovered = EvidenceJournal.replay(contents, expected_head=journal.head)
            closed = make_event(
                key="synthetic.file.recovery",
                claims=[fixture()[2][1]],
                status="closed",
                closure_claim_id=fixture()[2][1]["claim_id"],
            )
            with open(path, "a+", encoding="utf-8", newline="") as sink:
                self.assertEqual(recovered.append(sink, "event", closed, durable=True),
                                 "explicitly_closed")
            with open(path, encoding="utf-8") as src:
                again = EvidenceJournal.replay(src.read(), expected_head=recovered.head)
            self.assertEqual(again.ledger.counters()["event_versions"], 2)


if __name__ == "__main__":
    unittest.main()
