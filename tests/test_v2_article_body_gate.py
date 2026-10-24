"""A7: publisher body extraction, language, and geography must be source-grounded."""
import unittest
from v2_article_body_gate import extract_body, classify_geography, article_evidence

EN=(b'<html><head><title>Jordan report</title></head><body>'
    b'<nav><p>US weather advertising header</p></nav>'
    b'<article><h1>Seven shot dead at church funeral in Jordan</h1>'
    b'<p>Seven people have been killed in an attack on a funeral in Jordan, officials said.</p>'
    b'<p>At least 34 others were injured at the church in Jordan, the report added.</p>'
    b'<script>ignore dangerous script text</script>'
    b'</article><footer><p>Iran weather and markets advertisement</p></footer></body></html>')
AR=('''<html lang="ar"><body><main><h1>ارتفاع قتلى الهجوم في الأردن</h1>
    <div class="wysiwyg wysiwyg--all-content"><p>ارتفعت حصيلة قتلى الهجوم في كنيسة بمحافظة الكرك في الأردن بحسب السلطات المحلية.</p>
    <p>وقال مسؤولون أردنيون إن التحقيقات بشأن الهجوم ما تزال جارية.</p></div>
    <div class="loading-cards"><p>إعلانات لا علاقة لها بالخبر</p></div></main></body></html>''').encode('utf-8')

class BodyGateTests(unittest.TestCase):
    def test_bbc_article_content_anchor_excludes_site_chrome(self):
        result=extract_body(EN,source_url='https://www.bbc.co.uk/news/articles/example',language='en')
        self.assertEqual(result['extraction_basis'],'article_element')
        self.assertEqual(len(result['paragraphs']),2)
        self.assertNotIn('advertisement',result['original_text'])
        self.assertNotIn('dangerous script',result['original_text'])
        self.assertIn('Jordan',result['original_text'])
    def test_aljazeera_ar_wysiwyg_container(self):
        result=extract_body(AR,source_url='https://www.aljazeera.net/news/2026/10/24/jordan',language='ar')
        self.assertEqual(result['extraction_basis'],'aljazeera_article_wysiwyg')
        self.assertEqual(len(result['paragraphs']),2)
        self.assertNotIn('إعلانات',result['original_text'])
    def test_no_verified_container_is_refused(self):
        with self.assertRaisesRegex(ValueError,'article_body_container_missing'):
            extract_body(b'<html><p>Site headlines</p><p>Other paragraphs</p></html>',source_url='https://www.bbc.co.uk/news/articles/x',language='en')
    def test_over_budget_rejected(self):
        with self.assertRaisesRegex(ValueError,'html_size_out_of_bounds'):
            extract_body(b'x'*850001,source_url='https://www.bbc.co.uk/news/articles/x',language='en')
    def test_no_language_mismatch(self):
        with self.assertRaisesRegex(ValueError,'body_script_mismatch'):
            extract_body(EN,source_url='https://www.bbc.co.uk/news/articles/x',language='ar')
    def test_jordan_derived_from_title_and_body(self):
        body=extract_body(EN,source_url='https://www.bbc.co.uk/news/articles/example',language='en')
        geo=classify_geography('Seven shot dead at church funeral in Jordan',body['original_text'],language='en')
        self.assertEqual(geo['region'],'jordan')
        self.assertEqual(geo['subject_country'],'JO')
        self.assertEqual(geo['topic_english'],'security')
        self.assertEqual(geo['classification_status'],'headline_and_body_explicit_country')
    def test_multiple_headline_countries_withheld(self):
        with self.assertRaisesRegex(ValueError,'ambiguous_geography'):
            classify_geography('Jordan and Iran talks', 'Jordan and Iran met', language='en')
    def test_publisher_site_or_footer_not_a_location(self):
        with self.assertRaisesRegex(ValueError,'no_grounded_region'):
            classify_geography('Mysterious attack on Sunday', 'There was an attack according to officials.',language='en')
    def test_arabic_jordan_grounded(self):
        body=extract_body(AR,source_url='https://www.aljazeera.net/news/2026/10/24/jordan',language='ar')
        geo=classify_geography('ارتفاع قتلى الهجوم في الأردن',body['original_text'],language='ar')
        self.assertEqual(geo['region'],'jordan')
        self.assertEqual(geo['topic_arabic'],'security')
    def test_video_prompt_is_not_an_article_quote(self):
        page=EN.replace(b'<p>Seven people',b'<p>This video can not be played</p><p>Seven people')
        body=extract_body(page,source_url='https://www.bbc.co.uk/news/articles/example',language='en')
        ann=article_evidence(body,headline='Seven shot dead at church funeral in Jordan',published_at='2026-10-23T19:46:30+00:00')
        self.assertTrue(ann['quote'].startswith('Seven people'))
        self.assertNotIn('This video',body['original_text'])
    def test_article_evidence_keeps_headline_separate_and_short_quote(self):
        body=extract_body(EN,source_url='https://www.bbc.co.uk/news/articles/example',language='en')
        ann=article_evidence(body,headline='Seven shot dead at church funeral in Jordan',published_at='2026-10-23T19:46:30+00:00')
        self.assertLessEqual(len(ann['quote']),190)
        self.assertLessEqual(len(ann['quote'].split()),25)
        self.assertEqual(ann['body_sha256'],body['body_sha256'])
        self.assertEqual(ann['region'],'jordan')
        self.assertEqual(ann['publisher_factual_status'],'unverified_attributed')
