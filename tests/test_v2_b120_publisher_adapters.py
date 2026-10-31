import unittest
from v2_article_body_gate import extract_body
class PublisherAdapters(unittest.TestCase):
 def setUp(self):
  self.ar=('<html><body><article><p>أعلنت السلطات اليمنية اليوم عن إجراء محادثات أمنية جديدة في العاصمة مع وفود محلية لبحث الوضع الإنساني.</p><p>وأكدت الجهات المشاركة استمرار الاجتماعات في اليمن خلال الأسبوع الجاري مع متابعة النتائج لاحقاً.</p></article></body></html>').encode()
 def test_registry_publisher_article_allowed(self):
  r=extract_body(self.ar,source_url='https://www.france24.com/ar/story',language='ar')
  self.assertEqual(r['extraction_basis'],'article_element')
 def test_unlisted_host_denied(self):
  with self.assertRaisesRegex(ValueError,'unapproved_article_source'):
   extract_body(self.ar,source_url='https://evil.example/story',language='ar')
 def test_only_article_not_unrelated_page_paragraphs(self):
  h='<main><p>أعلنت السلطات اليمنية اليوم عن إجراء محادثات أمنية جديدة في العاصمة مع وفود محلية لبحث الوضع الإنساني.</p><p>وأكدت الجهات المشاركة استمرار الاجتماعات في اليمن خلال الأسبوع الجاري مع متابعة النتائج لاحقاً.</p></main>'
  with self.assertRaisesRegex(ValueError,'article_body_container_missing'):
   extract_body(h.encode(),source_url='https://www.france24.com/ar/story',language='ar')
 def test_wrong_script_denied(self):
  h='<article><p>Authorities in Yemen announced new security talks with delegations about current humanitarian conditions.</p><p>Officials said further meetings will continue next week with follow-up reporting expected.</p></article>'
  with self.assertRaisesRegex(ValueError,'body_script_mismatch'):
   extract_body(h.encode(),source_url='https://www.france24.com/ar/story',language='ar')
if __name__=='__main__':unittest.main()
