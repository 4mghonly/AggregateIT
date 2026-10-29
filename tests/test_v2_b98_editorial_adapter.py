import unittest
from v2_b98_editorial_adapter import compile_with_fallback
STAMP="2026-10-29T06:00:00+00:00"
def provider(name,host,source):
 return {"publisher_id":name,"product":"english","source_id":source,"article_url":"https://"+host+"/article","verified_article_host":host,"publisher_identity_verified":True,"feed_capture_verified":True,"article_body_gate_verified":True,"source_rights_reviewed":True,"live_article_evidence_eligible":True}
class AdapterTests(unittest.TestCase):
 def test_independent_source_cannot_be_mislabeled_as_bbc(self):
  p=provider("secondary","secondary.example","en-001")
  r=compile_with_fallback("primary",[p],as_of=STAMP,slot_id=STAMP)
  self.assertEqual(r["status"],"HOLD_PUBLISHER_NOT_ONBOARDED_IN_EDITORIAL_COMPILER")
  self.assertIsNone(r["editorial"])
 def test_claimed_eligible_but_invalid_article_bytes_are_held(self):
  p=provider("bbc","www.bbc.com","en-001")
  p["capture"]={"product":"english","source_id":"en-001","article_url":p["article_url"],"title":"Jordan government meeting today","published_at":STAMP,"html_bytes":b"<html>not an article</html>"}
  r=compile_with_fallback("bbc",[p],as_of=STAMP,slot_id=STAMP)
  self.assertEqual(r["status"],"HOLD_CAPTURE_EVIDENCE_INVALID")
  self.assertIsNone(r["editorial"])
 def test_unverified_source_never_compiles(self):
  p=provider("secondary","secondary.example","en-001");p["feed_capture_verified"]=False
  r=compile_with_fallback("primary",[p],as_of=STAMP,slot_id=STAMP)
  self.assertEqual(r["status"],"HOLD_NO_ELIGIBLE_PUBLISHER")
if __name__=="__main__":unittest.main()
