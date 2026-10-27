"""B36: caller-controlled flags must never become independent QA proof."""
import unittest
from v2_b27_private_acceptance import evaluate_private_acceptance


def nominal_flags():
    return {
        'admission': {'schema':'aggregateit-v2-b14-admission/1','admitted':[{'id':'synthetic'}]},
        'source_watch': {'schema':'aggregateit-v2-b15-watch/1','healthy_count':1},
        'parser_shadow': {'schema':'aggregateit-v2-b26-parser-shadow/1','parity_passed':True},
        'english_mobile': {'schema':'aggregateit-v2-b23-markup-audit/1','static_checks_passed':True},
        'arabic_mobile': {'schema':'aggregateit-v2-b23-markup-audit/1','static_checks_passed':True},
        'packet_rehearsal': {'schema':'aggregateit-v2-b22-packet-rehearsal/1','independent_destination_keys':True},
        'rollback': {'schema':'aggregateit-v2-b28-canary-rollback/1','rollback_acceptance':'TABLETOP_ONLY'},
    }


class EvidenceGateTests(unittest.TestCase):
    def test_no_self_reported_boolean_can_promote_external_acceptance(self):
        sample=nominal_flags()
        sample['parser_shadow']['live_parser_parity_proven']=True
        sample['english_mobile']['real_device_verified']=True
        sample['arabic_mobile']['real_device_verified']=True
        result=evaluate_private_acceptance(**sample)
        self.assertEqual(result['status'],'PARTIAL_OFFLINE')
        self.assertFalse(result['live_comparison_verified'])
        self.assertEqual(result['external_evidence_status'],'NOT_INDEPENDENTLY_VERIFIED')
        self.assertFalse(result['delivery_authorized'])

    def test_private_offline_path_remains_partial(self):
        result=evaluate_private_acceptance(**nominal_flags())
        self.assertEqual(result['status'],'PARTIAL_OFFLINE')
        self.assertFalse(result['live_comparison_verified'])

    def test_failed_core_check_holds_even_with_live_claims(self):
        sample=nominal_flags()
        sample['parser_shadow'].update(parity_passed=False,live_parser_parity_proven=True)
        sample['english_mobile']['real_device_verified']=True
        sample['arabic_mobile']['real_device_verified']=True
        result=evaluate_private_acceptance(**sample)
        self.assertEqual(result['status'],'HOLD')
        self.assertIn('same_input_parser_parity',result['unmet'])

    def test_bad_schema_refused(self):
        sample=nominal_flags()
        sample['admission']['schema']='wrong'
        with self.assertRaisesRegex(ValueError,'untrusted_private_acceptance_input'):
            evaluate_private_acceptance(**sample)


if __name__=='__main__': unittest.main()
