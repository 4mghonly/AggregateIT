import tempfile,unittest
from pathlib import Path
from v2_product_recovery import ProductHistory,build_weekly_intelligence
from v2_recovery_publication import render_recovery_html

class EditionAnalysisTests(unittest.TestCase):
 def test_preserves_attributed_arabic_executive_analysis(self):
  with tempfile.TemporaryDirectory() as d:
   h=ProductHistory(Path(d)/"history.sqlite")
   h.record_analysis("ar","2026-11-13","arabic_v2_model_unverified",{
    "situation_ar":"تقييم استراتيجي مستند إلى المادة المتاحة",
    "implications_ar":["انعكاس إقليمي محتمل"],"watch_ar":["مؤشر للمراقبة"]})
   report=build_weekly_intelligence(h,"ar","2026-11-13")
   self.assertEqual(report["historical_model_analysis"]["content"]["situation_ar"],"تقييم استراتيجي مستند إلى المادة المتاحة")
   self.assertIn("تقييم استراتيجي",render_recovery_html(report))
   self.assertIn("غير متحقق",render_recovery_html(report))
   h.close()
 def test_conflicting_analysis_is_not_silently_rewritten(self):
  with tempfile.TemporaryDirectory() as d:
   h=ProductHistory(Path(d)/"history.sqlite")
   h.record_analysis("ar","2026-11-13","arabic_v2_model_unverified",{"situation_ar":"original"})
   with self.assertRaises(ValueError):
    h.record_analysis("ar","2026-11-13","arabic_v2_model_unverified",{"situation_ar":"different"})
   h.close()
if __name__=="__main__":unittest.main()
