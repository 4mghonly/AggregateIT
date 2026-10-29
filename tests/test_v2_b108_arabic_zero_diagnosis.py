import unittest
from unittest.mock import patch
from v2_b46_live_editorial_runner import run
class ArabicZeroInvestigationTests(unittest.TestCase):
 def test_shadow_exposes_preselection_and_editorial_rejections(self):
  # Offline minimal feed snapshots; no publisher fetch and no Discord.
  snapshots={
   "english":{"feed_url":"https://feeds.bbci.co.uk/news/world/rss.xml","body":b"<rss><channel></channel></rss>"},
   "arabic":{"feed_url":"https://www.aljazeera.net/aljazeerarss/ar/all.xml","body":b"<rss><channel></channel></rss>"}}
  with patch("market.load_market_pulse",return_value={}),patch("market.load_macro_pulse",return_value={}):
   result=run(rss_snapshots=snapshots,render_native=False)
  self.assertIn("arabic_zero_story_diagnosis",result)
  diag=result["arabic_zero_story_diagnosis"]
  self.assertEqual(diag["status"],"HOLD_NO_ELIGIBLE_ARABIC_STORIES")
  self.assertIn("headline_country_unclassified",diag["counts"])
  self.assertIn("editorial_held_reasons",diag)
  self.assertFalse(result["can_release"])
if __name__=="__main__":unittest.main()
