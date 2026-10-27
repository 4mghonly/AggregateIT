"""B49 same-byte join, forged status and missing V1 final-product proof."""
import unittest
from v2_b49_single_slot_shadow import evaluate_shared_shadow

HASH='a'*64
def fixtures():
    parser={'schema':'aggregateit-v2-b38-exact-input/1','product':'english',
        'input_sha256':HASH,'parser_status':'MATCH','v1_reference_blob_verified':True,
        'v1_only_count':0,'v2_only_count':0,'can_publish':False}
    preview={'schema':'aggregateit-v2-b40-shared-input-headline-preview/1',
        'product':'english','capture_sha256':HASH,'identity_parity':True,'can_send':False}
    newsroom={'schema':'aggregateit-v2-b46-live-chain/1',
        'rss_feed_sha256':{'english':HASH},'rss_shared_snapshot_supplied':True,
        'editorial':{'products':{'english':{'story_count':2}}},
        'four_products':{'schema':'aggregateit-v2-b47-four-product-held/1'},
        'can_release':False}
    return parser,preview,newsroom

class SameSlotTests(unittest.TestCase):
    def test_exact_shared_rss_still_cannot_claim_complete_v1_v2_shadow(self):
        a,b,c=fixtures()
        result=evaluate_shared_shadow(a,b,c,expected_source_sha256=HASH,product='english')
        self.assertTrue(result['v1_v2_parser_parity'])
        self.assertTrue(result['v2_four_product_held'])
        self.assertFalse(result['actual_v1_full_native_rendered'])
        self.assertFalse(result['can_release'])
    def test_mismatched_candidate_rss_digest_refused(self):
        a,b,c=fixtures();c['rss_feed_sha256']['english']='b'*64
        with self.assertRaisesRegex(ValueError,'not_exact_same_source_bytes'):
            evaluate_shared_shadow(a,b,c,expected_source_sha256=HASH,product='english')
    def test_false_same_snapshot_flag_refused(self):
        a,b,c=fixtures();c['rss_shared_snapshot_supplied']=False
        with self.assertRaises(ValueError):
            evaluate_shared_shadow(a,b,c,expected_source_sha256=HASH,product='english')
    def test_parser_drift_is_measured_not_silently_accepted(self):
        a,b,c=fixtures();a['parser_status']='HOLD_MISMATCH'
        result=evaluate_shared_shadow(a,b,c,expected_source_sha256=HASH,product='english')
        self.assertFalse(result['v1_v2_parser_parity'])
        self.assertEqual(result['full_same_slot_comparison_status'],'HOLD_MISSING_V1_FULL_SYSTEM_EVIDENCE')
    def test_forged_release_permission_rejected(self):
        a,b,c=fixtures();a['can_publish']=True
        with self.assertRaisesRegex(ValueError,'forged_shadow_authority'):
            evaluate_shared_shadow(a,b,c,expected_source_sha256=HASH,product='english')
    def test_legacy_source_blob_must_be_pinned(self):
        a,b,c=fixtures();a['v1_reference_blob_verified']=False
        with self.assertRaisesRegex(ValueError,'unverified_legacy_reference_blob'):
            evaluate_shared_shadow(a,b,c,expected_source_sha256=HASH,product='english')
if __name__=='__main__':unittest.main()
