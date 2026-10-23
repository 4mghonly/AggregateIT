"""B3 portable, operator-signed head checkpoints; no real off-host service."""
import copy
from hashlib import sha256
import json
from tempfile import TemporaryDirectory
import unittest

from v2_evidence import make_article, make_excerpt
from v2_evidence_anchor import sign_anchor, verify_anchor
from v2_evidence_store import EvidenceStore


KEY = bytes(range(32))  # Synthetic TEST-ONLY key, never a deployment secret.
TIME = "2026-10-23T08:00:00+00:00"


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")


class ExternalAnchorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = TemporaryDirectory(prefix="aggregateit-v2-b3-anchor-")
        article = make_article(source_id="en-001", url="https://fixture.invalid/anchor",
                               original_text="Synthetic source checkpoint record.",
                               original_language="en", retrieved_at=TIME, published_at=TIME)
        excerpt = make_excerpt(article, 0, len(article["original_text"]))
        with EvidenceStore(cls.directory.name) as owner:
            owner.append("observe", article)
            cls.first_receipt = owner.journal.receipt()
            owner.append("excerpt", excerpt)
            cls.second_receipt = owner.journal.receipt()
        cls.first_anchor = sign_anchor(cls.first_receipt, secret=KEY,
                                       key_id="fixture-key-1", issued_at=TIME)
        cls.second_anchor = sign_anchor(
            cls.second_receipt, secret=KEY, key_id="fixture-key-1", issued_at=TIME,
            previous_anchor_sha256=sha256(canonical(cls.first_anchor)).hexdigest())

    @classmethod
    def tearDownClass(cls):
        cls.directory.cleanup()

    def test_authentic_first_and_chained_second_checkpoint(self):
        self.assertTrue(verify_anchor(self.first_anchor, self.first_receipt,
                                      secret=KEY, expected_key_id="fixture-key-1"))
        self.assertTrue(verify_anchor(self.second_anchor, self.second_receipt,
                                      secret=KEY, expected_key_id="fixture-key-1",
                                      previous_anchor=self.first_anchor))

    def test_third_checkpoint_can_reference_authenticated_second(self):
        third = sign_anchor(
            self.second_receipt, secret=KEY, key_id="fixture-key-1",
            issued_at="2026-10-23T09:00:00+00:00",
            previous_anchor_sha256=sha256(canonical(self.second_anchor)).hexdigest())
        self.assertTrue(verify_anchor(third, self.second_receipt,
                                      secret=KEY, expected_key_id="fixture-key-1",
                                      previous_anchor=self.second_anchor))

    def test_signed_but_out_of_order_head_rejected(self):
        backward = sign_anchor(
            self.first_receipt, secret=KEY, key_id="fixture-key-1",
            issued_at="2026-10-23T09:00:00+00:00",
            previous_anchor_sha256=sha256(canonical(self.second_anchor)).hexdigest())
        with self.assertRaisesRegex(ValueError, "anchor_sequence_rollback"):
            verify_anchor(backward, self.first_receipt, secret=KEY,
                          expected_key_id="fixture-key-1",
                          previous_anchor=self.second_anchor)

    def test_signed_same_sequence_with_different_head_is_a_fork(self):
        changed = copy.deepcopy(self.second_receipt)
        changed["head_sha256"] = "f" * 64
        fork = sign_anchor(changed, secret=KEY, key_id="fixture-key-1",
                           issued_at="2026-10-23T09:00:00+00:00",
                           previous_anchor_sha256=sha256(canonical(self.second_anchor)).hexdigest())
        with self.assertRaisesRegex(ValueError, "anchor_same_sequence_fork"):
            verify_anchor(fork, changed, secret=KEY,
                          expected_key_id="fixture-key-1", previous_anchor=self.second_anchor)

    def test_coherent_local_rollback_refused_by_newer_external_checkpoint(self):
        # Even if BOTH local journal and head were rolled back to earlier
        # mutually consistent bytes, the separately held second anchor fails.
        with self.assertRaisesRegex(ValueError, "external_anchor_receipt_mismatch"):
            verify_anchor(self.second_anchor, self.first_receipt,
                          secret=KEY, expected_key_id="fixture-key-1",
                          previous_anchor=self.first_anchor)

    def test_modified_anchor_rejected_even_if_receipt_still_valid(self):
        corrupted = copy.deepcopy(self.second_anchor)
        corrupted["receipt"]["seq"] = 1000
        with self.assertRaisesRegex(ValueError, "anchor_mac_mismatch"):
            verify_anchor(corrupted, self.second_receipt,
                          secret=KEY, expected_key_id="fixture-key-1",
                          previous_anchor=self.first_anchor)

    def test_wrong_key_or_key_identifier_rejected(self):
        with self.assertRaisesRegex(ValueError, "anchor_mac_mismatch"):
            verify_anchor(self.first_anchor, self.first_receipt,
                          secret=b"different-offline-test-key-at-least-32-bytes",
                          expected_key_id="fixture-key-1")
        with self.assertRaisesRegex(ValueError, "anchor_key_id_mismatch"):
            verify_anchor(self.first_anchor, self.first_receipt,
                          secret=KEY, expected_key_id="untrusted-key")

    def test_missing_or_wrong_external_predecessor_refused(self):
        with self.assertRaisesRegex(ValueError, "previous_external_anchor_required"):
            verify_anchor(self.second_anchor, self.second_receipt,
                          secret=KEY, expected_key_id="fixture-key-1")
        fake_previous = sign_anchor(self.first_receipt, secret=KEY,
                                    key_id="fixture-key-1", issued_at="2026-10-22T08:00:00+00:00")
        with self.assertRaisesRegex(ValueError, "anchor_chain_mismatch"):
            verify_anchor(self.second_anchor, self.second_receipt,
                          secret=KEY, expected_key_id="fixture-key-1",
                          previous_anchor=fake_previous)

    def test_short_key_and_naive_time_rejected(self):
        with self.assertRaisesRegex(ValueError, "32_byte"):
            sign_anchor(self.first_receipt, secret=b"short", key_id="x", issued_at=TIME)
        with self.assertRaisesRegex(ValueError, "invalid_anchor_issue_time"):
            sign_anchor(self.first_receipt, secret=KEY, key_id="fixture-key-1",
                        issued_at="2026-10-23T08:00:00")

    def test_anchor_records_no_signing_key_or_publisher_certification(self):
        raw = json.dumps(self.second_anchor)
        self.assertNotIn(KEY.hex(), raw)
        self.assertEqual(self.second_anchor["attestation"],
                         "operator_checkpoint_not_publisher_proof")


if __name__ == "__main__":
    unittest.main()
