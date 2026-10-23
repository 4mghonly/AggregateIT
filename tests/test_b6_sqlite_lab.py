"""B6 real SQLite :memory: lab; never touches a persistent user database."""
import copy
import unittest

from v2_analytics_sqlite_lab import InMemoryAnalytics
from test_b3_b7_offline_rehearsal import fixture, registry
from v2_offline_rehearsal import run_offline_rehearsal

NOW="2026-10-23T08:00:00+00:00"
OLD="2026-08-01T08:00:00+00:00"


def event(key="synthetic:arabic:edition", product="arabic", when=NOW):
    return {"idempotency_key":key,"kind":"edition","product":product,
            "at":when,"status":"withheld","units":1}


def write(lab,row,db=0,writes=0,reads=0):
    return lab.ingest(row,account_db_bytes=db,
                      account_writes_today=writes,
                      account_reads_today=reads)


class SqliteLabTests(unittest.TestCase):
    def test_unknown_account_headroom_refuses_optional_storage(self):
        lab=InMemoryAnalytics()
        result=lab.ingest(event(),account_db_bytes=None,
                          account_writes_today=None,account_reads_today=None)
        self.assertFalse(result["db_written"])
        self.assertEqual(result["reason"],"hold_unverified_account_headroom")
        self.assertEqual(lab.count(),0)

    def test_bounded_local_write_and_idempotent_retry(self):
        lab=InMemoryAnalytics()
        r=write(lab,event())
        self.assertEqual(r["status"],"accepted_local_only")
        self.assertFalse(r["external_d1_written"])
        self.assertEqual(write(lab,event())["status"],"already_recorded")
        self.assertEqual(lab.count(),1)

    def test_same_idempotency_with_changed_body_rejected(self):
        lab=InMemoryAnalytics()
        write(lab,event())
        altered={**event(),"status":"failed"}
        with self.assertRaisesRegex(ValueError,"conflicting_analytics_idempotency"):
            write(lab,altered)

    def test_budget_holds_throttle_stop_and_daily_limits(self):
        for db,writes,reads,expected in (
            (300_000_000,0,0,"throttle_detail"),
            (350_000_000,0,0,"stop_optional_analytics"),
            (0,20_000,0,"stop_usage_budget"),
            (0,0,250_000,"stop_usage_budget"),
        ):
            lab=InMemoryAnalytics()
            self.assertEqual(write(lab,event(),db=db,writes=writes,reads=reads)["reason"],expected)
            self.assertEqual(lab.count(),0)


    def test_stale_account_snapshot_cannot_hide_sequential_writes(self):
        lab=InMemoryAnalytics()
        first=write(lab,event("synthetic:one"),writes=19_999)
        self.assertEqual(first["status"],"accepted_local_only")
        second=write(lab,event("synthetic:two"),writes=19_999)
        self.assertEqual(second["status"],"withheld_optional_analytics")
        self.assertEqual(second["reason"],"stop_usage_budget")
        self.assertEqual(lab.count(),1)

    def test_raw_articles_and_secret_fields_rejected(self):
        lab=InMemoryAnalytics()
        for bad in ("raw_text","url","api_key","prompt"):
            with self.subTest(bad=bad),self.assertRaisesRegex(ValueError,"unapproved_fields"):
                write(lab,{**event(),bad:"sensitive"})
        self.assertEqual(lab.count(),0)

    def test_bilingual_grouped_metrics_no_source_text(self):
        lab=InMemoryAnalytics()
        write(lab,event())
        write(lab,event("synthetic:english:edition","english"))
        self.assertEqual(lab.count(),2)
        self.assertEqual([(x["product"],x["count"]) for x in lab.metrics()],
                         [("arabic",1),("english",1)])
        self.assertNotIn("raw_text",str(lab.rows()))

    def test_export_restore_exact_metadata_with_checksum(self):
        lab=InMemoryAnalytics()
        write(lab,event())
        write(lab,event("synthetic:english:edition","english"))
        bundle=lab.export_bytes(as_of=NOW)
        self.assertEqual(bundle["row_count"],2)
        self.assertFalse(bundle["drive_uploaded"])
        proof=InMemoryAnalytics.verify_restore(bundle)
        self.assertTrue(proof["checksum_verified"])
        self.assertTrue(proof["in_memory_restore_only"])
        self.assertFalse(proof["external_database_written"])
        self.assertEqual(proof["restored_local_rows"],2)
        self.assertEqual(lab.count(),2)

    def test_tampered_export_bytes_refused(self):
        lab=InMemoryAnalytics()
        write(lab,event())
        bundle=lab.export_bytes(as_of=NOW)
        bundle["payload"]+=b"X"
        with self.assertRaisesRegex(ValueError,"checksum_mismatch"):
            InMemoryAnalytics.verify_restore(bundle)

    def test_cannot_fake_drive_or_production_backup(self):
        lab=InMemoryAnalytics()
        bundle=lab.export_bytes(as_of=NOW)
        bundle["drive_uploaded"]=True
        with self.assertRaisesRegex(ValueError,"fake_external_backup"):
            InMemoryAnalytics.verify_restore(bundle)

    def test_cleanup_stays_dry_run_after_backup_rehearsal(self):
        lab=InMemoryAnalytics()
        write(lab,event("synthetic:old:edition","arabic",OLD))
        write(lab,event("synthetic:new:edition","english"))
        self.assertEqual(InMemoryAnalytics.verify_restore(lab.export_bytes(as_of=NOW))["restored_local_rows"],2)
        dry=lab.retention_dry_run(as_of=NOW)
        self.assertEqual(dry["mode"],"DRY_RUN_ONLY")
        self.assertEqual(dry["candidate_ids"],["synthetic:old:edition"])
        self.assertFalse(dry["delete_authorized"])
        self.assertEqual(lab.count(),2)


    def test_bilingual_no_post_rehearsal_metrics_roundtrip(self):
        no_post=run_offline_rehearsal(fixture(),registry())
        lab=InMemoryAnalytics()
        for product in ("english","arabic"):
            receipt=write(lab,no_post["products"][product]["telemetry"])
            self.assertEqual(receipt["status"],"accepted_local_only")
        self.assertEqual(lab.count(),2)
        self.assertEqual({r["product"] for r in lab.metrics()},{"english","arabic"})
        proof=InMemoryAnalytics.verify_restore(lab.export_bytes(as_of=NOW))
        self.assertEqual(proof["restored_local_rows"],2)
        self.assertFalse(no_post["discord_sent"])

    def test_invalid_backup_timestamp_refused(self):
        lab=InMemoryAnalytics()
        with self.assertRaisesRegex(ValueError,"bad_timestamp"):
            lab.export_bytes(as_of="not-a-timestamp")

if __name__=="__main__":
    unittest.main()
