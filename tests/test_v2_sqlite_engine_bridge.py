import tempfile,unittest
from pathlib import Path
from v2_sqlite_engine_bridge import save_receipt
from v2_sqlite_store import Store
class BridgeTests(unittest.TestCase):
 def test_persist_without_article_bodies(self):
  receipt={"schema":"aggregateit-v2-b46-live-chain/1","observed_at":"2026-10-28T00:00:00+00:00","discord_sent":False,"can_release":False,"rss_feed_sha256":{"english":"a","arabic":"b"},"source_attempts":{"english":{"feed_ok":True,"article_attempts":3,"article_http_ok":3,"article_evidence_eligible":2},"arabic":{"feed_ok":True,"article_attempts":4,"article_http_ok":4,"article_evidence_eligible":1}},"editorial":{"products":{"english":{"story_count":2},"arabic":{"story_count":1}}},"native":{"status":"HELD_VALID_NATIVE_PAGES"}}
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/"a.sqlite"
   save_receipt(receipt,p);save_receipt(receipt,p)
   with Store(p) as db:
    self.assertEqual(db.count("source_health"),2)
    self.assertEqual(db.count("edition_evidence"),2)
    self.assertEqual(db.count("articles"),0)
 def test_rejects_release_receipt(self):
  with tempfile.TemporaryDirectory() as t:
   with self.assertRaises(ValueError):save_receipt({"schema":"aggregateit-v2-b46-live-chain/1","discord_sent":True,"can_release":False},Path(t)/"a.sqlite")
if __name__=="__main__":unittest.main()
