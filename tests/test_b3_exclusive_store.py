"""No-post, no-database B3 cooperative lock and crash-window fault probes."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from v2_evidence import make_article, make_excerpt, make_claim, make_event
from v2_evidence_store import EvidenceStore


def fixture():
    stamp = "2026-10-23T08:00:00+00:00"
    article = make_article(
        source_id="ar-s056", url="https://example.org/synthetic-exclusive-owner",
        original_text="بيان عربي تجريبي محفوظ", original_language="ar",
        retrieved_at=stamp, published_at=stamp,
    )
    excerpt = make_excerpt(article, 0, len(article["original_text"]))
    claim = make_claim(statement="تحديث أمني من مصدر تجريبي", excerpts=[excerpt])
    event = make_event(key="synthetic.exclusive.owner", claims=[claim])
    return (("observe", article), ("excerpt", excerpt),
            ("claim", claim), ("event", event))


class ExclusiveStoreTests(unittest.TestCase):
    def directory(self):
        return tempfile.TemporaryDirectory(prefix="aggregateit-b3-lock-", dir="/tmp")

    def test_create_reopen_and_exact_unicode_fsync_receipt(self):
        with self.directory() as root:
            with EvidenceStore(root) as owner:
                for kind, payload in fixture():
                    owner.append(kind, payload)
                observed = owner.journal.receipt()
                self.assertEqual(observed["seq"], 4)
                self.assertEqual(observed["counters"]["events"], 1)
            with EvidenceStore(root) as owner:
                self.assertEqual(owner.journal.receipt(), observed)
                self.assertEqual(owner.journal.bytes_written, os.stat(owner.log_path).st_size)

    def test_second_same_process_owner_refused(self):
        with self.directory() as root:
            with EvidenceStore(root):
                with self.assertRaisesRegex(RuntimeError, "writer_busy"):
                    with EvidenceStore(root):
                        pass
            with EvidenceStore(root):
                pass

    def test_separate_process_owner_refused(self):
        with self.directory() as root:
            with EvidenceStore(root):
                script = ("from v2_evidence_store import EvidenceStore; "
                          "import sys; "
                          "store=EvidenceStore(sys.argv[1]); "
                          "store.__enter__()")
                environment = dict(os.environ, PYTHONPATH=str(Path(__file__).resolve().parents[1]))
                result = subprocess.run([sys.executable, "-B", "-c", script, root],
                                        env=environment, capture_output=True, text=True, timeout=10)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("evidence_writer_busy", result.stderr)

    def test_crash_after_journal_sync_before_receipt_refuses_reopen(self):
        with self.directory() as root:
            with EvidenceStore(root) as owner:
                owner.append(*fixture()[0])
                with patch.object(owner, "_write_receipt", side_effect=OSError("injected_receipt_failure")):
                    with self.assertRaisesRegex(OSError, "injected_receipt_failure"):
                        owner.append(*fixture()[1])
                with self.assertRaisesRegex(RuntimeError, "requires_recovery"):
                    owner.append(*fixture()[2])
            with self.assertRaisesRegex(ValueError, "receipt_mismatch"):
                with EvidenceStore(root):
                    pass

    def test_modified_receipt_fails_before_any_append(self):
        with self.directory() as root:
            with EvidenceStore(root) as owner:
                owner.append(*fixture()[0])
            path = Path(root) / "evidence.head.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            data["receipt"]["seq"] = 7
            path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "checksum_mismatch"):
                with EvidenceStore(root):
                    pass

    def test_complete_tail_loss_refused_even_with_valid_receipt(self):
        with self.directory() as root:
            with EvidenceStore(root) as owner:
                for item in fixture():
                    owner.append(*item)
            log = Path(root) / "evidence.jsonl"
            lines = log.read_text(encoding="utf-8").splitlines(keepends=True)
            log.write_text("".join(lines[:-1]), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "receipt_mismatch"):
                with EvidenceStore(root):
                    pass

    def test_torn_tail_refused_without_truncation(self):
        with self.directory() as root:
            with EvidenceStore(root) as owner:
                owner.append(*fixture()[0])
            log = Path(root) / "evidence.jsonl"
            with open(log, "a", encoding="utf-8") as stream:
                stream.write('{"v":1')
            previous = log.read_bytes()
            with self.assertRaisesRegex(ValueError, "journal_truncated_tail"):
                with EvidenceStore(root):
                    pass
            self.assertEqual(log.read_bytes(), previous)

    def test_missing_pair_refused_without_recreation(self):
        with self.directory() as root:
            (Path(root) / "evidence.jsonl").write_text("", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "pair_missing"):
                with EvidenceStore(root):
                    pass
            self.assertFalse((Path(root) / "evidence.head.json").exists())

    def test_invalid_preflight_does_not_poison_valid_next_append(self):
        with self.directory() as root:
            with EvidenceStore(root) as owner:
                with self.assertRaisesRegex(ValueError, "unsupported_journal_command"):
                    owner.append("unsupported", {"noise": True})
                self.assertEqual(owner.journal.seq, 0)
                owner.append(*fixture()[0])
                self.assertEqual(owner.journal.seq, 1)
            with EvidenceStore(root) as recovered:
                self.assertEqual(recovered.journal.seq, 1)


if __name__ == "__main__":
    unittest.main()
