"""B40 authentic bytes preview parity without native/model/delivery overclaims."""
import unittest
from unittest.mock import patch
import v2_b40_shared_preview as m
RAW=b'<rss><channel><title>Fixture</title></channel></rss>'
NOW='2026-10-27T06:00:00+00:00'
URL='https://example.org/rss'
TITLE='Test world regional policy announcement'
URL2='https://example.org/news/story'
DATE='2026-10-27T05:00:00+00:00'
TS=1793077200
def row():return {'title':TITLE,'url':URL2,'ts':TS,'published':TS}
def extracted(title=TITLE):
    return {'items':[{'title':title,'article_url':URL2,'source_feed_url':URL,'published_at':DATE}],
            'candidate_count':1}
class SharedPreviewTests(unittest.TestCase):
    def test_same_content_no_false_native_assertion(self):
        from datetime import datetime
        when=datetime.fromisoformat(DATE).timestamp()
        with (patch.object(m,'_verified_v1_code',return_value=True),
              patch.object(m,'_v1_rows',return_value=[{'title':TITLE,'url':URL2,'ts':when,'published':when}]) as legacy,
              patch.object(m,'extract_candidates',return_value=extracted()) as v2):
            x=m.compare_previews(RAW,product='english',feed_url=URL,observed_at=NOW)
        self.assertIs(legacy.call_args.args[0],RAW)
        self.assertIs(v2.call_args.args[0],RAW)
        self.assertTrue(x['identity_parity'])
        self.assertEqual(x['v1_eligible'],1)
        self.assertFalse(x['editorial_selection_comparable'])
        self.assertFalse(x['external_delivery_comparable'])
        self.assertNotIn(TITLE,str(x))
    def test_changed_title_produces_drift(self):
        from datetime import datetime
        ts=datetime.fromisoformat(DATE).timestamp()
        with (patch.object(m,'_verified_v1_code',return_value=True),
              patch.object(m,'_v1_rows',return_value=[{'title':TITLE,'url':URL2,'ts':ts}]),
              patch.object(m,'extract_candidates',return_value=extracted('Different region title from V2'))):
            x=m.compare_previews(RAW,product='english',feed_url=URL,observed_at=NOW)
        self.assertFalse(x['identity_parity'])
        self.assertEqual(x['v1_only_count'],1)
        self.assertEqual(x['v2_only_count'],1)
    def test_arabic_but_non_arabic_headline_is_filtered_at_display(self):
        from datetime import datetime
        ts=datetime.fromisoformat(DATE).timestamp()
        with (patch.object(m,'_verified_v1_code',return_value=True),
              patch.object(m,'_v1_rows',return_value=[{'title':TITLE,'url':URL2,'published':ts}]),
              patch.object(m,'extract_candidates',return_value=extracted())):
            x=m.compare_previews(RAW,product='arabic',feed_url=URL,observed_at=NOW)
        self.assertTrue(x['identity_parity'])
        self.assertEqual(x['v2_source_headline_cards'],0)
    def test_legacy_blob_drift_fails_closed(self):
        with patch.object(m,'_verified_v1_code',return_value=False):
            with self.assertRaisesRegex(ValueError,'legacy_parser_drift'):
                m.compare_previews(RAW,product='english',feed_url=URL,observed_at=NOW)
    def test_reject_insecure_source_or_missing_bytes(self):
        for body,url in [(RAW,'http://example.org/rss'),(b'',URL)]:
            with self.assertRaises(ValueError):
                m.compare_previews(body,product='english',feed_url=url,observed_at=NOW)
if __name__=='__main__':unittest.main()
