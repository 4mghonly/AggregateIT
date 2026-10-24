"""B11 country coverage must not be certified from feed reachability alone."""
import unittest
from v2_b11_coverage_readiness import assess_source_regions, TARGET_REGIONS

def obs(sid,region,language,status='usable_dated_feed',host='news.example.org',native=False):
    return {'source_id':sid,'region':region,'language':language,'status':status,
            'feed_url':'https://'+host+'/feed','arabic_original_language_candidate':native,
            'publication_rights_verified':False,'publisher_independence_verified':False}

class RegionReadinessTests(unittest.TestCase):
    def test_english_feed_on_arabic_stream_not_native_arabic(self):
        r=assess_source_regions([obs('ar-s017','gcc','en')])
        gcc=r['regions']['gcc']
        self.assertEqual(gcc['usable_feeds'],1)
        self.assertEqual(gcc['native_arabic_feed_candidates'],0)
        self.assertFalse(gcc['editorial_coverage_verified'])
        self.assertFalse(r['release_authorized'])

    def test_somalia_two_english_alternatives_and_somali_are_not_arabic(self):
        feeds=[obs('ar-s056','somalia','so',host='radioergo.org'),
               obs('soma-b1','somalia','en',host='shabellemedia.com'),
               obs('soma-b2','somalia','en',host='somaliguardian.com')]
        r=assess_source_regions(feeds)['regions']['somalia']
        self.assertEqual(r['usable_feeds'],3)
        self.assertEqual(r['native_arabic_feed_candidates'],0)
        self.assertFalse(r['independent_publisher_families_verified'])

    def test_duplicate_ids_not_double_counted(self):
        r=assess_source_regions([obs('x','jordan','ar',native=True),obs('x','jordan','ar',native=True)])
        self.assertEqual(r['regions']['jordan']['usable_feeds'],1)

    def test_two_sources_same_host_cannot_be_called_independent(self):
        r=assess_source_regions([obs('x1','jordan','ar',native=True),obs('x2','jordan','ar',native=True)])
        self.assertEqual(r['regions']['jordan']['host_candidates'],1)
        self.assertFalse(r['regions']['jordan']['independent_publisher_families_verified'])

    def test_invalid_source_status_does_not_count(self):
        feeds=[obs('x1','yemen','ar',status='http_403',native=True),
               obs('x2','yemen','ar',status='oversized_body',native=True)]
        r=assess_source_regions(feeds)['regions']['yemen']
        self.assertEqual(r['usable_feeds'],0)
        self.assertEqual(r['tested_sources'],2)

    def test_empty_region_is_unprobed_not_zero_fresh(self):
        r=assess_source_regions([])
        self.assertEqual(r['regions']['north_africa']['status'],'not_tested')
        self.assertIn('north_africa',r['unproven_regions'])
        self.assertEqual(len(TARGET_REGIONS),17)

    def test_unknown_region_fails_closed(self):
        with self.assertRaisesRegex(ValueError,'unrecognized_region'):
            assess_source_regions([obs('x','antarctica','en')])

    def test_all_regions_populated_still_no_release_without_article_independence_rights(self):
        feeds=[obs('s'+str(i),region,'ar',native=True,host='s'+str(i)+'.example.org')
               for i,region in enumerate(TARGET_REGIONS)]
        r=assess_source_regions(feeds)
        self.assertEqual(len(r['regions']),len(TARGET_REGIONS))
        self.assertFalse(r['release_authorized'])
        self.assertTrue(all(not value['editorial_coverage_verified'] for value in r['regions'].values()))

if __name__=='__main__':unittest.main()
