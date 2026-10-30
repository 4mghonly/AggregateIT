"""B114: precise Arabic-topic acceptance; reject unrelated and ambiguous items."""
import unittest
from v2_article_body_gate import classify_geography
from v2_event_intelligence import arabic_filter

class ArabicTopicPrecisionTests(unittest.TestCase):
 def test_security_with_prefixed_and_inflected_arabic_is_admitted(self):
  headline="السودان: والقصف المدفعي يستهدف مواقع قرب الحدود"
  lead="أكدت السلطات في السودان أن القصف المدفعي وقع قرب المنطقة الحدودية."
  result=classify_geography(headline,lead,language="ar")
  self.assertEqual(result["topic_arabic"],"security")
  self.assertTrue(arabic_filter(headline+" "+lead,region=result["region"],headline=headline,lead=lead)["admit"])

 def test_explicit_diplomacy_without_security_words_is_admitted(self):
  headline="السودان يستضيف محادثات دبلوماسية بشأن العلاقات الإقليمية"
  lead="أعلنت الحكومة في السودان إجراء المحادثات مع وفود من بلدان المنطقة."
  result=classify_geography(headline,lead,language="ar")
  self.assertEqual(result["topic_arabic"],"diplomacy")
  self.assertTrue(arabic_filter(headline+" "+lead,region=result["region"],headline=headline,lead=lead)["admit"])

 def test_article_lead_security_cue_can_support_neutral_country_headline(self):
  headline="السودان: تطورات جديدة صباح اليوم"
  lead="أكدت السلطات في السودان وقوع اشتباكات مسلحة قرب الحدود وأعلنت تفاصيل الهجوم."
  result=classify_geography(headline,lead,language="ar")
  self.assertEqual(result["topic_arabic"],"security")
  self.assertTrue(arabic_filter(headline+" "+lead,region=result["region"],headline=headline,lead=lead)["admit"])

 def test_routine_government_service_decision_not_promoted(self):
  headline="قرار حكومي جديد بشأن الخدمات في السودان"
  lead="أعلنت إدارة السودان إصدار قرار حكومي يتعلق بالخدمات العامة وتطوير المنشآت."
  self.assertFalse(arabic_filter(headline+" "+lead,region="sudan",headline=headline,lead=lead)["admit"])

 def test_unrelated_cultural_story_remains_rejected(self):
  headline="مهرجان ثقافي جديد في السودان"
  lead="أعلن المنظمون في السودان إقامة مهرجان موسيقي وفني."
  self.assertFalse(arabic_filter(headline+" "+lead,region="sudan",headline=headline,lead=lead)["admit"])

 def test_geography_not_derived_from_unverified_mentions(self):
  headline="تطورات جديدة في المنطقة"
  lead="أعلنت السلطات عن تطورات دون تسمية أي بلد."
  with self.assertRaisesRegex(ValueError,"no_grounded_region"):
   classify_geography(headline,lead,language="ar")

 def test_multiple_countries_still_refused(self):
  headline="تطورات أمنية مهمة"
  lead="أكدت السلطات في السودان واليمن وقوع اشتباكات قرب الحدود."
  with self.assertRaisesRegex(ValueError,"ambiguous_geography"):
   classify_geography(headline,lead,language="ar")

 def test_missing_region_is_not_admitted(self):
  self.assertFalse(arabic_filter("القصف على الحدود",region=None)["admit"])

if __name__=="__main__":unittest.main()
