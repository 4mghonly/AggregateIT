import tempfile,unittest
from pathlib import Path
from v2_b129_artifact_store import store_day
SHA="b67a9e4115f4f88049716d608e54a6d06ef5f15f"
class Tests(unittest.TestCase):
 def test_store_real_files_and_no_overwrite(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);sources={}
   for p in ("english","arabic"):
    files=[]
    for ext,content in [("html",b"<html>authored analysis</html>"),("pdf",b"%PDF-1.4 test"),("json",b'{"analysis":"authored"}')]:
     f=root/(p+"."+ext);f.write_bytes(content);files.append(f)
    sources[p]=files
   receipt=store_day(root/"archive",utc_date="2026-11-13",head_sha=SHA,run_id="42178164780",capture_sha256="a"*64,source_files=sources,story_identities={p:["e"*64] for p in sources})
   self.assertEqual(receipt["utc_date"],"2026-11-13")
   self.assertTrue((root/"archive"/"2026-11-13"/"english"/"daily.html").is_file())
   with self.assertRaises(FileExistsError):store_day(root/"archive",utc_date="2026-11-13",head_sha=SHA,run_id="42178164780",capture_sha256="a"*64,source_files=sources,story_identities={p:["e"*64] for p in sources})
 def test_missing_file_fails_without_archive(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp)
   with self.assertRaises((ValueError,FileNotFoundError)):
    store_day(root/"archive",utc_date="2026-11-13",head_sha=SHA,run_id="1",capture_sha256="a"*64,source_files={"english":[],"arabic":[]},story_identities={})
   self.assertFalse((root/"archive"/"2026-11-13").exists())
if __name__=="__main__":unittest.main()
