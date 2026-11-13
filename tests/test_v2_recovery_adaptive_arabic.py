import unittest
from arabic_layout.render_pages import page3_category_plan

class AdaptiveArabicPageTests(unittest.TestCase):
 def test_empty_categories_omitted(self):
  brief={"events":[{"fingerprint":"x","region":"iran","title_ar":"قرار دبلوماسي","summary_ar":"محادثات دبلوماسية","topic":"diplomacy"}]}
  plan=page3_category_plan(brief)
  self.assertTrue(plan)
  self.assertFalse(any(not x["rows"] for x in plan))
  self.assertTrue(any(x["title"]=="الأقاليم الجغرافية" for x in plan))
  self.assertFalse(any(x["title"]=="التوترات البحرية" for x in plan))
 def test_empty_brief_does_not_invent_category(self):
  self.assertEqual(page3_category_plan({"events":[]}),[])
if __name__=="__main__":unittest.main()
