import unittest
from v2_b98_independent_fallback import route
def publisher(name,ok=True,verified=True):
 return {"publisher_id":name,"article_url":"https://"+name+".example/article","verified_article_host":name+".example","publisher_identity_verified":verified,"feed_capture_verified":verified,"article_body_gate_verified":verified,"source_rights_reviewed":verified,"live_article_evidence_eligible":ok}
class IndependentFallbackTests(unittest.TestCase):
 def test_primary_failure_secondary_success(self):
  r=route("primary",[publisher("primary",False),publisher("secondary")])
  self.assertEqual(r["selected_publisher"],"secondary")
  self.assertTrue(r["independent_fallback_used"])
  self.assertFalse(r["can_release"])
 def test_unverified_secondary_never_used(self):
  r=route("primary",[publisher("primary",False),publisher("secondary",True,False)])
  self.assertIsNone(r["selected_publisher"])
 def test_mismatched_domain_refused(self):
  p=publisher("primary");p["verified_article_host"]="wrong.example"
  with self.assertRaises(ValueError):route("primary",[p])
 def test_budget_bounded(self):
  r=route("primary",[publisher(str(i),False) for i in range(5)],max_candidates=2)
  self.assertLessEqual(len(r["attempts"]),2)
if __name__=="__main__":unittest.main()
