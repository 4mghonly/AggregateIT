"""B13: region-balanced newsletters remain rights-held and readable."""
import unittest
from v2_b13_balance import balance_held_news

BASE = ['gcc','oman','iran','turkey','iraq','yemen','sudan','sahel','north_africa',
        'egypt','pakistan','afghanistan','somalia','horn','palestine_israel','levant','jordan']

def candidate(region='gcc', source='s1', index=1, priority=70, lang='ar', country='AE', topic='security'):
    return {'event_id':f'evt_{index}', 'region':region,'source_id':source,
            'original_language':lang,'subject_country':country,'topic':topic,
            'priority':priority,'headline':f'Test-only item {index}',
            'synthetic':True,'rights_status':'unresolved','source_url':'https://example.org/news'}

class BalanceRules(unittest.TestCase):
    def test_uae_first_arabic_then_distinct_regions(self):
        a=[candidate('yemen','s1',1,99,country='YE'),candidate('gcc','s2',2,50,country='AE'),
           candidate('iran','s3',3,80,country='IR'),candidate('yemen','s1',4,88,country='YE')]
        out=balance_held_news(a,product='arabic',max_tiles=3)
        self.assertEqual(out['tiles'][0]['region'],'gcc')
        self.assertEqual(set(x['region'] for x in out['tiles']),{'gcc','iran','yemen'})
        self.assertFalse(out['delivery_authorized'])
    def test_english_does_not_monopolize_with_one_high_priority_region(self):
        a=[candidate('gcc','s1',i,100-i,lang='en') for i in range(1,5)]
        a+=[candidate('sudan','s5',8,54,lang='en',country='SD'),
            candidate('yemen','s6',9,54,lang='en',country='YE')]
        out=balance_held_news(a,product='english',max_tiles=3)
        self.assertEqual(set(x['region'] for x in out['tiles']),{'gcc','sudan','yemen'})
    def test_arabic_language_guard_excludes_persian(self):
        a=[candidate('iran','s1',1,lang='fa',country='IR'),
           candidate('yemen','s2',2,lang='ar',country='YE')]
        out=balance_held_news(a,product='arabic',max_tiles=3)
        self.assertEqual(len(out['tiles']),1)
        self.assertEqual(out['withheld_non_native'],1)
    def test_unlicensed_real_article_never_reproduces_excerpt(self):
        a=candidate()
        a['synthetic']=False
        a['headline']='Potential copyrighted publisher headline'
        out=balance_held_news([a],product='arabic')
        self.assertEqual(out['tiles'][0]['display_headline'],'حقوق إعادة النشر غير مؤكدة')
        self.assertNotIn(a['headline'],str(out))
        self.assertFalse(out['rights_cleared'])
    def test_synthetic_text_can_be_displayed_as_synthetic_only(self):
        a=candidate(lang='en')
        out=balance_held_news([a],product='english')
        self.assertEqual(out['tiles'][0]['display_headline'],a['headline'])
        self.assertTrue(out['tiles'][0]['synthetic'])
        self.assertFalse(out['delivery_authorized'])
    def test_reject_duplicate_event_ids(self):
        a=candidate()
        with self.assertRaisesRegex(ValueError,'duplicate_event_id'):
            balance_held_news([a,a],product='arabic')
    def test_over_capacity_records_without_claiming_full_coverage(self):
        a=[candidate(x,f's{i}',i,80-i,country='AE' if x=='gcc' else 'JO') for i,x in enumerate(BASE,1)]
        out=balance_held_news(a,product='arabic',max_tiles=6)
        self.assertEqual(len(out['tiles']),6)
        self.assertEqual(out['omitted_due_to_space'],11)
        self.assertEqual(len(out['unrepresented_target_regions']),11)
        self.assertFalse(out['editorial_coverage_verified'])
    def test_no_real_article_copyright_bypass_from_input_label(self):
        a=candidate(lang='en')
        a['synthetic']=False;a['rights_status']='explicit_licensed'
        out=balance_held_news([a],product='english')
        self.assertFalse(out['rights_cleared'])
        self.assertNotEqual(out['tiles'][0]['display_headline'],a['headline'])
    def test_bad_region_and_bad_url_rejected(self):
        a=candidate('bad-region')
        with self.assertRaises(ValueError):balance_held_news([a],product='english')
        a=candidate(lang='en');a['source_url']='javascript:alert(1)'
        with self.assertRaises(ValueError):balance_held_news([a],product='english')
