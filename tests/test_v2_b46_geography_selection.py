"""B46 TDD: explicitly grounded country/title prefilter and exact country body match."""
import unittest
from v2_article_body_gate import headline_geography_candidates,classify_geography

class ExpandedCountryTests(unittest.TestCase):
    def test_single_israel_country_in_headline_body(self):
        x=classify_geography('Israel officials held consultations',
                             'Israel officials met in Tel Aviv after talks.',language='en')
        self.assertEqual(x['region'],'palestine_israel')
        self.assertEqual(x['subject_country'],'IL')
    def test_palestinian_gaza_not_falsely_israeli(self):
        x=classify_geography('Gaza officials issue statement',
                             'Officials in Gaza released the statement.',language='en')
        self.assertEqual(x['subject_country'],'PS')
    def test_duplicate_region_gcc_qatar_uses_correct_country_pattern(self):
        x=classify_geography('Qatar officials discussed regional policy',
                             'Qatar ministers met in Doha to discuss policy.',language='en')
        self.assertEqual(x['region'],'gcc')
        self.assertEqual(x['subject_country'],'QA')
    def test_bbc_multiple_countries_still_held(self):
        with self.assertRaisesRegex(ValueError,'ambiguous_geography'):
            classify_geography('Israel and Gaza officials met', 'Israel and Gaza met',language='en')
    def test_lebanese_diplomatic_arabic_context(self):
        x=classify_geography('مباحثات دبلوماسية في لبنان',
                            'قال مسؤولون في لبنان إن المباحثات مستمرة.',language='ar')
        self.assertEqual(x['region'],'levant')
        self.assertEqual(x['subject_country'],'LB')
        self.assertEqual(x['topic_arabic'],'diplomacy')
    def test_prefilter_does_not_assign_no_country(self):
        self.assertEqual(headline_geography_candidates('World markets open Monday',language='en'),[])
    def test_region_requires_body_grounding(self):
        with self.assertRaisesRegex(ValueError,'country_not_supported_by_article_body'):
            classify_geography('Lebanon officials met','Other leaders met elsewhere',language='en')
    def test_multiple_gcc_subjects_fail_closed(self):
        with self.assertRaisesRegex(ValueError,'ambiguous_geography'):
            classify_geography('Qatar and Saudi Arabia leaders met','Qatar and Saudi Arabia met',language='en')
if __name__=='__main__':unittest.main()
