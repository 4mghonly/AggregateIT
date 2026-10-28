import tempfile,unittest
from pathlib import Path
from v2_b86_visual_archive import validate_page_archive
class VisualArchiveTests(unittest.TestCase):
 def test_missing_page_fails_closed(self):
  with tempfile.TemporaryDirectory() as d:
   with self.assertRaises(ValueError):validate_page_archive(Path(d))
 def test_non_png_fails_closed(self):
  with tempfile.TemporaryDirectory() as d:
   for language,count in (("english",2),("arabic",3)):
    for n in range(1,count+1):
     (Path(d)/f"{language}-no-post-{n}.png").write_bytes(b"not png")
   with self.assertRaises(ValueError):validate_page_archive(Path(d))
if __name__=="__main__":unittest.main()
