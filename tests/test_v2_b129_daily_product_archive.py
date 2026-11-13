import unittest
from datetime import date,timedelta
from v2_b129_daily_product_archive import make_snapshot,verify_week
SHA="b67a9e4115f4f88049716d608e54a6d06ef5f15f"
def sample(day):
 return make_snapshot(utc_date=day,head_sha=SHA,run_id="42178164780",capture_sha256="a"*64,
    products={p:{"daily_html_sha256":"b"*64,"daily_pdf_sha256":"c"*64,
       "editorial_payload_sha256":"d"*64,"story_identities":["e"*64],
       "market_data_evidence":"NOT_VERIFIED","translation_evidence":"NOT_VERIFIED",
       "publisher_rights":"UNVERIFIED","rendered":True} for p in ("english","arabic")})
class Tests(unittest.TestCase):
 def test_seven_unique_dates_still_requires_independent_acceptance(self):
  days=[(date(2026,11,6)+timedelta(days=i)).isoformat() for i in range(7)]
  x=verify_week([sample(d) for d in days],expected_sha=SHA)
  self.assertTrue(x["seven_daily_snapshots_verified"])
  self.assertFalse(x["full_weekly_product_parity_verified"])
  self.assertFalse(x["can_release"])
 def test_six_days_not_full_week(self):
  days=[(date(2026,11,6)+timedelta(days=i)).isoformat() for i in range(6)]
  self.assertFalse(verify_week([sample(d) for d in days],expected_sha=SHA)["seven_daily_snapshots_verified"])
 def test_duplicate_date_rejected(self):
  d="2026-11-06"
  self.assertFalse(verify_week([sample(d)]*7,expected_sha=SHA)["seven_daily_snapshots_verified"])
 def test_digest_tamper_rejected(self):
  days=[(date(2026,11,6)+timedelta(days=i)).isoformat() for i in range(7)]
  rows=[sample(d) for d in days];rows[0]["products"]["english"]["daily_html_sha256"]="f"*64
  self.assertFalse(verify_week(rows,expected_sha=SHA)["seven_daily_snapshots_verified"])
 def test_missing_language_rejected(self):
  with self.assertRaises(ValueError):make_snapshot(utc_date="2026-11-06",head_sha=SHA,run_id="1",capture_sha256="a"*64,products={"english":{}})
 def test_no_publisher_text(self):
  p={k:{"daily_html_sha256":"b"*64,"daily_pdf_sha256":"c"*64,"editorial_payload_sha256":"d"*64,"story_identities":["e"*64],"market_data_evidence":"NOT_VERIFIED","translation_evidence":"NOT_VERIFIED","publisher_rights":"UNVERIFIED","rendered":True} for k in ("english","arabic")}
  p["english"]["article_body"]="copyrighted"
  with self.assertRaises(ValueError):make_snapshot(utc_date="2026-11-06",head_sha=SHA,run_id="1",capture_sha256="a"*64,products=p)
 def test_wrong_sha_rejected(self):
  days=[(date(2026,11,6)+timedelta(days=i)).isoformat() for i in range(7)]
  self.assertFalse(verify_week([sample(d) for d in days],expected_sha="f"*40)["seven_daily_snapshots_verified"])
if __name__=="__main__":unittest.main()
