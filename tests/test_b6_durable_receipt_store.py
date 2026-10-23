"""B6 local receipt durability/ambiguity rehearsal; no network or database."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from hashlib import sha256

from v2_delivery_receipt_store import DurableReceiptStore


SLOT = "2026-10-23T06:00:00+04:00"
EN = dict(product="english", slot_id=SLOT, destination_key="discord_webhook",
          edition_digest="a" * 64)
AR = dict(product="arabic", slot_id=SLOT, destination_key="discord_webhook_arabic",
          edition_digest="b" * 64)


class DurableReceiptTests(unittest.TestCase):
    def test_restart_preserves_ambiguous_outcome_and_prevents_retry(self):
        with tempfile.TemporaryDirectory(prefix="aggregateit-b6-receipt-") as root:
            with DurableReceiptStore(root) as store:
                self.assertTrue(store.reserve(**EN))
                store.mark_network_attempt(product="english", slot_id=SLOT)
                self.assertFalse(store.retry_allowed(product="english", slot_id=SLOT))
            with DurableReceiptStore(root) as recovered:
                self.assertFalse(recovered.reserve(**EN))
                self.assertEqual(recovered.snapshot(product="english", slot_id=SLOT)["state"],
                                 "ambiguous_network_outcome")
                self.assertFalse(recovered.retry_allowed(product="english", slot_id=SLOT))

    def test_two_product_receipts_are_independently_durable(self):
        with tempfile.TemporaryDirectory(prefix="aggregateit-b6-receipt-") as root:
            with DurableReceiptStore(root) as store:
                store.reserve(**EN)
                store.reserve(**AR)
                store.mark_network_attempt(product="arabic", slot_id=SLOT)
                store.record_confirmed_receipt(product="arabic", slot_id=SLOT,
                                               destination_key="discord_webhook_arabic",
                                               message_id="synthetic-789")
            with DurableReceiptStore(root) as recovered:
                self.assertTrue(recovered.retry_allowed(product="english", slot_id=SLOT))
                self.assertFalse(recovered.retry_allowed(product="arabic", slot_id=SLOT))
                self.assertEqual(recovered.snapshot(product="arabic", slot_id=SLOT)["state"],
                                 "confirmed_unverified")
                self.assertIn("requires_external", recovered.snapshot(product="arabic", slot_id=SLOT)["receipt_provenance"])

    def test_second_writer_refused_without_touching_existing_data(self):
        with tempfile.TemporaryDirectory(prefix="aggregateit-b6-receipt-") as root:
            with DurableReceiptStore(root) as first:
                first.reserve(**EN)
                original = (Path(root) / "delivery.receipts.json").read_bytes()
                with self.assertRaisesRegex(RuntimeError, "receipt_writer_busy"):
                    with DurableReceiptStore(root):
                        pass
                self.assertEqual(original, (Path(root) / "delivery.receipts.json").read_bytes())

    def test_corrupt_checksum_and_missing_state_fail_closed(self):
        with tempfile.TemporaryDirectory(prefix="aggregateit-b6-receipt-") as root:
            with DurableReceiptStore(root) as store:
                store.reserve(**EN)
            state = Path(root) / "delivery.receipts.json"
            original = state.read_bytes()
            parsed = json.loads(original)
            parsed["body"]["rows"][0]["edition_digest"] = "f" * 64
            state.write_text(json.dumps(parsed), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "receipt_state_checksum_mismatch"):
                with DurableReceiptStore(root):
                    pass
            state.write_bytes(original)
            state.unlink()
            with self.assertRaisesRegex(ValueError, "receipt_state_missing"):
                with DurableReceiptStore(root):
                    pass

    def test_persist_failure_poisoned_before_any_external_attempt(self):
        with tempfile.TemporaryDirectory(prefix="aggregateit-b6-receipt-") as root:
            with DurableReceiptStore(root) as store:
                store.reserve(**EN)
                before = (Path(root) / "delivery.receipts.json").read_bytes()
                with patch.object(store, "_write_state", side_effect=OSError("synthetic_io_failure")):
                    with self.assertRaisesRegex(OSError, "synthetic_io_failure"):
                        store.mark_network_attempt(product="english", slot_id=SLOT)
                with self.assertRaisesRegex(RuntimeError, "receipt_store_requires_recovery"):
                    store.retry_allowed(product="english", slot_id=SLOT)
                self.assertEqual(before, (Path(root) / "delivery.receipts.json").read_bytes())
            with DurableReceiptStore(root) as recovered:
                self.assertTrue(recovered.retry_allowed(product="english", slot_id=SLOT))

    def test_symlinked_state_and_lock_are_refused(self):
        with tempfile.TemporaryDirectory(prefix="aggregateit-b6-receipt-") as root:
            with DurableReceiptStore(root):
                pass
            state = Path(root) / "delivery.receipts.json"
            saved = Path(root) / "kept.json"
            state.rename(saved)
            state.symlink_to(saved)
            with self.assertRaisesRegex(ValueError, "receipt_store_symlink_refused"):
                with DurableReceiptStore(root):
                    pass
            self.assertTrue(saved.is_file())

    def test_wrong_destination_or_duplicate_content_rejected_after_restart(self):
        with tempfile.TemporaryDirectory(prefix="aggregateit-b6-receipt-") as root:
            with DurableReceiptStore(root) as store:
                store.reserve(**EN)
            with DurableReceiptStore(root) as recovered:
                with self.assertRaisesRegex(ValueError, "different_content"):
                    recovered.reserve(**{**EN, "edition_digest": "c" * 64})
                with self.assertRaisesRegex(ValueError, "destination_mismatch"):
                    recovered.reserve(**{**AR, "destination_key": "discord_webhook"})

    def test_abrupt_process_exit_preserves_attempt_marker(self):
        with tempfile.TemporaryDirectory(prefix="aggregateit-b6-receipt-") as root:
            script = (
                "import os,sys; from v2_delivery_receipt_store import DurableReceiptStore; "
                "s=DurableReceiptStore(sys.argv[1]); s.__enter__(); "
                "s.reserve(product='english',slot_id='2026-10-23T06:00:00+04:00',"
                "destination_key='discord_webhook',edition_digest='a'*64); "
                "s.mark_network_attempt(product='english',slot_id='2026-10-23T06:00:00+04:00'); "
                "os._exit(0)"
            )
            environment = dict(os.environ, PYTHONPATH=str(Path(__file__).resolve().parents[1]))
            process = subprocess.run([sys.executable, "-B", "-c", script, root],
                                     env=environment, capture_output=True, timeout=10)
            self.assertEqual(process.returncode, 0, process.stderr.decode("utf-8", "replace"))
            with DurableReceiptStore(root) as recovered:
                self.assertEqual(recovered.snapshot(product="english", slot_id=SLOT)["state"],
                                 "ambiguous_network_outcome")
                self.assertFalse(recovered.retry_allowed(product="english", slot_id=SLOT))

    def test_valid_checksum_cannot_authorize_forged_external_receipt(self):
        with tempfile.TemporaryDirectory(prefix="aggregateit-b6-receipt-") as root:
            with DurableReceiptStore(root) as store:
                store.reserve(**EN)
            state = Path(root) / "delivery.receipts.json"
            payload = json.loads(state.read_text(encoding="utf-8"))
            payload["body"]["rows"][0]["state"] = "confirmed_external"
            raw_body = json.dumps(payload["body"], ensure_ascii=False, sort_keys=True,
                                  separators=(",", ":")).encode("utf-8")
            payload["checksum_sha256"] = sha256(raw_body).hexdigest()
            state.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "invalid_receipt_state_row"):
                with DurableReceiptStore(root):
                    pass

    def test_slot_ceiling_survives_restart(self):
        with tempfile.TemporaryDirectory(prefix="aggregateit-b6-receipt-") as root:
            with DurableReceiptStore(root, max_slots=1) as store:
                store.reserve(**EN)
            with DurableReceiptStore(root, max_slots=1) as recovered:
                with self.assertRaisesRegex(ValueError, "slot_ceiling"):
                    recovered.reserve(**AR)


if __name__ == "__main__":
    unittest.main()
