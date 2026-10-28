import unittest
from v2_article_body_gate import classify_geography
class ArabicTopicTests(unittest.TestCase):
 def test_economic_diplomatic_headline_is_geopolitics(self):
  r=classify_geography("إيران تعلن اتفاقا اقتصاديا جديدا","أعلنت إيران عن اتفاق اقتصادي جديد مع شركات محلية.",language="ar")
  self.assertEqual(r["topic_arabic"],"geopolitics")
 def test_geopolitical_event_maps_to_allowed_arabic_topic(self):
  from v2_b87_topic_bridge import editorial_topic
  self.assertEqual(editorial_topic('arabic','geopolitics'),'political_stability')
  self.assertEqual(editorial_topic('arabic','diplomacy'),'diplomacy')
  self.assertEqual(editorial_topic('arabic','security'),'security')
 def test_unrelated_headline_still_fails(self):
  with self.assertRaises(ValueError):classify_geography("إيران في الأخبار","تحدثت إيران عن موضوع عام.",language="ar")
if __name__=="__main__":unittest.main()
