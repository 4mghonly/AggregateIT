"""B122 verifies offline routing, idempotency and rollback HOLD, not Discord."""
import tempfile
import unittest
from pathlib import Path
from v2_b122_no_send_delivery_audit import audit_no_send_delivery

class NoSendDeliveryAuditTests(unittest.TestCase):
    def test_production_cadence_and_destinations_preserved_without_sending(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)/'rehearsal';root.mkdir()
            result=audit_no_send_delivery(Path('.'),root,
                                         slot_id='2026-11-06T07:00:00+00:00')
            self.assertTrue(result['v1_schedule_continuity_checked'])
            self.assertTrue(result['v2_distinct_destination_keys'])
            self.assertTrue(result['ambiguous_network_outcome_persisted'])
            self.assertTrue(result['blind_retry_refused'])
            self.assertTrue(result['wrong_channel_refused'])
            self.assertFalse(result['authenticated_v1_v2_delivery_parity_verified'])
            self.assertFalse(result['discord_sent'])
            self.assertFalse(result['production_modified'])
            self.assertFalse(result['can_release'])

if __name__ == '__main__':
    unittest.main()
