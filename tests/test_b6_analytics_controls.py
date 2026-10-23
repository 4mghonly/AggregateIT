"""B6 budget and scheduled-cleanup DRY RUN only: no Cloudflare calls."""
import unittest

from v2_analytics_controls import (
    validate_telemetry, budget_decision, retention_preview, export_manifest,
)

NOW = "2026-10-23T06:00:00+00:00"
GOOD = {"idempotency_key": "synthetic:edition:001",
        "kind": "edition", "product": "arabic", "at": NOW,
        "status": "degraded", "units": 1}


class AnalyticsTests(unittest.TestCase):
    def test_metadata_record_accepts_allowlisted_fields(self):
        self.assertEqual(validate_telemetry(GOOD), GOOD)

    def test_reject_raw_article_prompt_url_and_secret(self):
        for key in ("raw_text", "url", "prompt", "api_key", "provider_response"):
            with self.subTest(key=key), self.assertRaisesRegex(ValueError,"unapproved_fields"):
                validate_telemetry({**GOOD, key: "raw-sensitive-data"})

    def test_unknown_headroom_fails_closed(self):
        result = budget_decision(db_size_bytes=None, account_writes_today=0,
                                 account_reads_today=0, proposed_writes=1, proposed_reads=10)
        self.assertFalse(result["permitted"])
        self.assertEqual(result["action"], "hold_unverified_account_headroom")

    def test_warn_at_250mb(self):
        result = budget_decision(db_size_bytes=250_000_000,account_writes_today=0,
                         account_reads_today=0,proposed_writes=1,proposed_reads=10)
        self.assertTrue(result["permitted"])
        self.assertEqual(result["action"],"warn_and_aggregate")

    def test_throttle_detail_at_300mb_but_allow_aggregates(self):
        args = dict(db_size_bytes=300_000_000, account_writes_today=0,
                    account_reads_today=0, proposed_writes=1, proposed_reads=10)
        self.assertFalse(budget_decision(**args,detail=True)["permitted"])
        self.assertTrue(budget_decision(**args,detail=False)["permitted"])

    def test_stop_at_350mb(self):
        x = budget_decision(db_size_bytes=350_000_000,account_writes_today=0,
                    account_reads_today=0,proposed_writes=1,proposed_reads=10,detail=False)
        self.assertFalse(x["permitted"])
        self.assertEqual(x["action"],"stop_optional_analytics")

    def test_daily_write_and_read_ceiling(self):
        args=dict(db_size_bytes=10,account_writes_today=19_999,
                  account_reads_today=249_990,proposed_writes=2,proposed_reads=5)
        self.assertFalse(budget_decision(**args)["permitted"])
        args.update(account_writes_today=0, proposed_writes=1, proposed_reads=20)
        self.assertFalse(budget_decision(**args)["permitted"])

    def test_retention_dry_run_preserves_input_and_never_deletes(self):
        rows = [
            {"id":"a","at":"2026-09-01T00:00:00Z","retention_class":"detail"},
            {"id":"b","at":"2026-10-22T00:00:00Z","retention_class":"detail"},
            {"id":"c","at":"2025-01-01T00:00:00Z","retention_class":"daily_aggregate"},
        ]
        snapshot = list(rows)
        result = retention_preview(rows, as_of=NOW)
        self.assertEqual(result["candidate_ids"], ["a","c"])
        self.assertEqual(rows,snapshot)
        self.assertFalse(result["delete_authorized"])
        self.assertEqual(result["scheduled_hour_uae"], "04:30")

    def test_untrusted_retention_rows_refused(self):
        with self.assertRaises(ValueError):
            retention_preview([{"id":"a","at":NOW,"retention_class":"raw_article"}],as_of=NOW)

    def test_export_manifest_does_not_claim_backup_or_restore(self):
        m = export_manifest([GOOD], as_of=NOW)
        self.assertEqual(m["records"],1)
        self.assertEqual(len(m["sha256"]),64)
        self.assertFalse(m["verified_restore"])
        self.assertFalse(m["google_drive_uploaded"])

    def test_no_raw_fields_in_manifest(self):
        m = export_manifest([GOOD], as_of=NOW)
        self.assertNotIn("raw_text",m)
        self.assertNotIn("idempotency_key",m)

    def test_negative_usage_denied(self):
        with self.assertRaises(ValueError):
            budget_decision(db_size_bytes=0,account_writes_today=0,
                            account_reads_today=0,proposed_writes=-1,proposed_reads=0)


if __name__ == "__main__":
    unittest.main()
