import json
import unittest
from hashlib import sha256
from v2_b124_editorial_review_queue import build_review_queue, assess_analyst_reviews

class EditorialReviewQueueTests(unittest.TestCase):
    def test_runner_creates_disagreement_queue_without_raw_publisher_content(self):
        from test_v2_replacement_pipeline import AT, fake_fetch, snapshots
        from v2_b46_live_editorial_runner import run
        output=run(rss_snapshots=snapshots(),observed_at=AT,fetch=fake_fetch,
                   compare_same_capture=True,market_snapshot={})
        queue=output['b124_editorial_review_queue']
        self.assertEqual(queue['schema'],'aggregateit-v2-b124-editorial-disagreement-review/1')
        self.assertNotIn('Somalia security officials',json.dumps(queue,ensure_ascii=False))
        self.assertFalse(queue['can_release'])

    def test_v1_only_article_is_linked_without_publisher_text(self):
        url='https://www.example.org/news/event?utm_source=test'
        from v2_evidence import canonical_article_url
        identity=sha256(canonical_article_url(url).encode()).hexdigest()
        paired={'schema':'aggregateit-v2-b115-same-capture/1','can_release':False,
                'observed_at':'2026-11-06T07:00:00+00:00','products':{
                'english':{'per_article':[{'identity_sha256':identity,'v1_selected':True,
                   'v2_selected':False,'v2_decision_stage':'rejected_body_or_evidence',
                   'v2_decision_reason':'article_body_container_missing',
                   'v2_preselection_rank':None}]},
                'arabic':{'per_article':[]}}}
        capture={'product':'english','source_id':'en-001','article_url':url,
                 'title':'Proprietary publisher headline',
                 'html_bytes':b'Proprietary publisher article body'}
        q=build_review_queue(paired,[capture])
        self.assertEqual(q['unadjudicated'],1)
        self.assertEqual(q['rows'][0]['v2_rejection_reason'],'article_body_container_missing')
        self.assertEqual(q['rows'][0]['source_url'],canonical_article_url(url))
        self.assertNotIn('Proprietary',json.dumps(q))
        self.assertFalse(q['can_release'])
        review=assess_analyst_reviews(q,[])
        self.assertEqual(review['status'],'HOLD_ANALYST_ADJUDICATION_REQUIRED')

if __name__=='__main__':unittest.main()
