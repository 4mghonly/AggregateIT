import tempfile,unittest,sqlite3
from pathlib import Path
from v2_sqlite_store import Store,MAX_DB_BYTES
class SQLiteStoreTests(unittest.TestCase):
 def test_roundtrip_and_deduplicate(self):
  with tempfile.TemporaryDirectory() as t:
   with Store(Path(t)/"store.db") as db:
    db.put("articles","en","https://example.org/a",{"title":"A"},observed_at="2026-10-28T00:00:00+00:00")
    db.put("articles","en","https://example.org/a",{"title":"B"},observed_at="2026-10-28T00:00:00+00:00")
    self.assertEqual(db.count("articles"),1)
    self.assertEqual(db.get("articles","en","https://example.org/a")["title"],"B")
 def test_rejects_invalid_table_and_large_payload(self):
  with tempfile.TemporaryDirectory() as t:
   with Store(Path(t)/"store.db") as db:
    with self.assertRaises(ValueError): db.count("sqlite_master")
    with self.assertRaises(ValueError): db.put("articles","en","x",{"x":"z"*200000})
 def test_retention_does_not_remove_new_rows(self):
  with tempfile.TemporaryDirectory() as t:
   with Store(Path(t)/"store.db") as db:
    db.put("source_health","en","old",{"ok":True},observed_at="2026-01-01T00:00:00+00:00")
    db.put("source_health","en","new",{"ok":True},observed_at="2026-10-28T00:00:00+00:00")
    self.assertEqual(db.cleanup("2026-10-28T00:00:00+00:00"),1)
    self.assertEqual(db.count("source_health"),1)
 def test_schema_has_no_secrets(self):
  with tempfile.TemporaryDirectory() as t:
   with Store(Path(t)/"store.db") as db:
    self.assertLess(db.size_bytes(),MAX_DB_BYTES)
    self.assertEqual(db.count("edition_evidence"),0)
if __name__=="__main__":unittest.main()
