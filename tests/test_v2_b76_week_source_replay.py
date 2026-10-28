import unittest
from datetime import datetime,timedelta,timezone
from v2_b61_week_lineage import evaluate_week_lineage
GST=timezone(timedelta(hours=4))
class SourceReplayTests(unittest.TestCase):
    def test_replayed_source_snapshot_fails_week(self):
        rows=[]
        for product in ("english","arabic"):
            for i in range(7):
                day=datetime(2026,10,28,12,tzinfo=GST)-timedelta(days=i)
                rows.append({"product":product,"slot_id":day.isoformat(),
                    "origin":"original_source_capture","held":True,"production_sent":False,
                    "edition_sha256":format(i+(100 if product=="arabic" else 0),"064x"),
                    "source_snapshot_sha256":"a"*64})
        r=evaluate_week_lineage(rows,as_of="2026-10-28T19:00:00+04:00")
        self.assertFalse(r["seven_distinct_days_structurally_present"])
        self.assertIn("reused_identical_source_snapshot_digest",r["duplicate_or_replay_issues"])
    def test_distinct_source_snapshots_structurally_pass(self):
        rows=[]
        for product in ("english","arabic"):
            for i in range(7):
                day=datetime(2026,10,28,12,tzinfo=GST)-timedelta(days=i)
                n=i+(100 if product=="arabic" else 0)
                rows.append({"product":product,"slot_id":day.isoformat(),
                    "origin":"original_source_capture","held":True,"production_sent":False,
                    "edition_sha256":format(n,"064x"),
                    "source_snapshot_sha256":format(n+500,"064x")})
        r=evaluate_week_lineage(rows,as_of="2026-10-28T19:00:00+04:00")
        self.assertTrue(r["seven_distinct_days_structurally_present"])
        self.assertFalse(r["can_release"])
if __name__=="__main__":unittest.main()
