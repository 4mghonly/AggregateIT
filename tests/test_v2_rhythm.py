"""Tests for V2 planning-only six-hour UAE rhythm."""
import unittest
from v2_rhythm import daily_slots,weekly_slot
class RhythmTests(unittest.TestCase):
    def test_four_daily_slots_six_hours_apart(self):
        rows=daily_slots('2026-10-24')
        self.assertEqual([r['local_hour'] for r in rows],[0,6,12,18])
        self.assertEqual([r['full_morning'] for r in rows],[False,True,False,False])
        self.assertTrue(all(r['slot_id'].endswith('+04:00') for r in rows))
        self.assertTrue(all(r['schedule_enabled'] is False for r in rows))
    def test_weekly_sunday_is_proposal_only(self):
        x=weekly_slot('2026-10-25')
        self.assertEqual(x['local_hour'],6)
        self.assertEqual(x['cadence'],'weekly')
        self.assertFalse(x['schedule_enabled'])
    def test_wrong_weekday_refused(self):
        with self.assertRaises(ValueError):weekly_slot('2026-10-24')
    def test_bad_date_formats_refused(self):
        for s in ('2026-10-33','2026-10-24T06:00:00','2026/10/24'):
            with self.assertRaises(ValueError):daily_slots(s)

if __name__=='__main__':unittest.main()
