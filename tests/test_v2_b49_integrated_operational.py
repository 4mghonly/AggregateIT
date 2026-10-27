"""B49 one capture reused across B47/B48/B49: no false production promotion."""
import unittest
from hashlib import sha256
from unittest.mock import patch
from v2_b49_single_slot_shadow import run_one_slot

class CombinedShadowTests(unittest.TestCase):
    def test_partial_shadow_and_ops_share_two_captured_feeds(self):
        raw=b'<rss>mock-source</rss>';digest=sha256(raw).hexdigest()
        def network(url,**kwargs):
            return {'body':raw,'final_url':url,'status':200}
        def parser(raw,*,product,feed_url,observed_at):
            return {'schema':'aggregateit-v2-b38-exact-input/1','product':product,
                    'input_sha256':digest,'parser_status':'MATCH',
                    'v1_reference_blob_verified':True,'v1_only_count':0,'v2_only_count':0,
                    'can_publish':False}
        def preview(raw,*,product,feed_url,observed_at):
            return {'schema':'aggregateit-v2-b40-shared-input-headline-preview/1',
                    'product':product,'capture_sha256':digest,'identity_parity':True,
                    'can_send':False}
        def newsroom(*,render_four_products,rss_snapshots,observed_at):
            self.assertTrue(render_four_products)
            self.assertEqual({k:sha256(v['body']).hexdigest() for k,v in rss_snapshots.items()},
                             {'english':digest,'arabic':digest})
            return {'schema':'aggregateit-v2-b46-live-chain/1',
                'rss_feed_sha256':{'english':digest,'arabic':digest},
                'rss_shared_snapshot_supplied':True,'editorial':{'products':{
                  'english':{'story_count':1},'arabic':{'story_count':1}}},
                'four_products':{'schema':'aggregateit-v2-b47-four-product-held/1'},
                'can_release':False}
        with (patch('v2_b49_single_slot_shadow.pinned_https_fetch',side_effect=network) as f,
              patch('v2_b49_single_slot_shadow.compare_captured_headlines',side_effect=parser),
              patch('v2_b49_single_slot_shadow.compare_previews',side_effect=preview),
              patch('v2_b49_single_slot_shadow.run',side_effect=newsroom),
              patch('v2_b41_production_preflight.inspect_workflows',return_value={'schema':'mock'}),
              patch('v2_b39_rollback_rehearsal.exercise_durable_no_send',return_value={'schema':'mock'}),
              patch('v2_b48_operations_readiness.evaluate_operations',
                    return_value={'can_release':False,'alerts':[{'code':'incomplete'}]})):
            result=run_one_slot(production_baseline='/tmp/read-only-main',candidate_root='/tmp/candidate')
        self.assertEqual(f.call_count,2)
        self.assertTrue(result['same_live_capture_used_for_b47_b48_b49'])
        self.assertEqual(len(result['rows']),2)
        self.assertEqual(result['operational_preflight']['alerts'][0]['code'],'incomplete')
        self.assertFalse(result['v1_v2_full_editorial_model_render_delivery_matched'])
        self.assertFalse(result['can_release'])
    def test_one_sided_prod_path_rejected(self):
        with self.assertRaises(ValueError):
            run_one_slot(production_baseline='/tmp/only-baseline')
if __name__=='__main__':unittest.main()
