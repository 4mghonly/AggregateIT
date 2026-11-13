import tempfile,unittest
from pathlib import Path
from PIL import Image
from v2_recovery_english_layout import render_english_held

class EnglishLayoutTests(unittest.TestCase):
 def test_two_real_evidence_pages_without_empty_market_panels(self):
  items=[{"region":"iran","topic":"security","evidence":{"quote":f"Attributed security development {i} with relevant context","source_id":"bbc","source_url":"https://example.org/article"}} for i in range(6)]
  with tempfile.TemporaryDirectory() as d:
   paths=render_english_held({"product":"english","items":items},d)
   self.assertEqual(len(paths),2)
   for path in paths:
    self.assertTrue(path.is_file())
    with Image.open(path) as im:self.assertEqual(im.size,(3840,2160))
 def test_empty_edition_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   with self.assertRaises(ValueError):render_english_held({"product":"english","items":[]},d)
if __name__=="__main__":unittest.main()
