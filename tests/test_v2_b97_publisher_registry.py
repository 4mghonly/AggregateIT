import unittest
from v2_b97_publisher_registry import evaluate
class RegistryTests(unittest.TestCase):
 def test_empty_registry_never_claims_redundancy(self):
  r=evaluate([])
  self.assertFalse(r["independent_fallback_available"]["arabic"])
  self.assertFalse(r["can_release"])
 def test_unverified_feed_held(self):
  r=evaluate([{"publisher_id":"source2","language":"arabic","feed_url":"https://example.com/rss","publisher_identity_verified":True,"feed_capture_verified":True,"article_body_gate_verified":False,"source_rights_reviewed":True}])
  self.assertIn("source2",r["held_publishers"])
 def test_duplicate_identity_rejected(self):
  p={"publisher_id":"same","language":"english","feed_url":"https://example.com/rss"}
  with self.assertRaises(ValueError):evaluate([p,p])
if __name__=="__main__":unittest.main()
