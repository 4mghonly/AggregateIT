import unittest
from datetime import datetime,timezone
from cadence_gate import slot_start,duplicate

class ScheduledSlot(unittest.TestCase):
    def test_uae_six_hour_slots_and_daily_gazette(self):
        now=datetime(2026,10,14,13,30,tzinfo=timezone.utc).timestamp()
        self.assertEqual(datetime.fromtimestamp(slot_start('arabic-scheduler.yml',now),timezone.utc).hour,8)
        self.assertEqual(datetime.fromtimestamp(slot_start('slide.yml',now),timezone.utc).hour,11)
    def test_native_delayed_run_cannot_repeat_successful_external_slot(self):
        now=datetime(2026,10,14,14,30,tzinfo=timezone.utc).timestamp()
        run={'id':1,'status':'completed','conclusion':'success','created_at':'2026-10-14T14:05:00Z'}
        self.assertTrue(duplicate([run],'arabic-scheduler.yml',now,current_id=2))
        self.assertFalse(duplicate([run],'arabic-scheduler.yml',now,current_id=1))
        self.assertFalse(duplicate([{**run,'conclusion':'failure'}],'arabic-scheduler.yml',now,current_id=2))
    def test_old_edition_does_not_block_new_slot(self):
        now=datetime(2026,10,14,14,30,tzinfo=timezone.utc).timestamp()
        run={'id':1,'status':'completed','conclusion':'success','created_at':'2026-10-14T08:05:00Z'}
        self.assertFalse(duplicate([run],'arabic-scheduler.yml',now,current_id=2))
