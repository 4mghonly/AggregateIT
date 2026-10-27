"""B40 guard tests: synthetically green pieces cannot promote full-system acceptance."""
import unittest
from v2_b40_stage_acceptance import assess_full_shadow

def fixture():
    capture={'schema':'aggregateit-v2-b38-live-parser-pair/1','status':'COMPARED',
             'parity_all':True,'results':[{'product':'english','status':'COMPARED'},
                                           {'product':'arabic','status':'COMPARED'}]}
    pages=[{'product':p,'page':i,'sha256':('a' if p=='english' else 'b')*64}
           for p,count in [('english',2),('arabic',3)] for i in range(1,count+1)]
    native={'schema':'aggregateit-v2-native-no-post-pages/1', 'pages':pages,
            'delivery_authorized':False,'discord_sent':False,'llm_called':False,
            'source_facts_verified':False}
    packets={p:{'schema':'aggregateit-v2-discord-preview/1','product':p,
                'destination_key':'discord_webhook_arabic' if p=='arabic' else 'discord_webhook',
                'message_count':1,'can_send':False,'synthetic':True,'webhook_url':None,
                'attachments':[{'sha256':('a' if p=='english' else 'b')*64,'size_bytes':100} for _ in range(c)]}
             for p,c in [('english',2),('arabic',3)]}
    return capture,native,packets

class B40StageTests(unittest.TestCase):
    def test_live_parser_plus_synthetic_pages_never_pretend_full_comparison(self):
        r=assess_full_shadow(*fixture())
        self.assertTrue(r['stage_evidence']['live_exact_input_v1_v2_parsers'])
        self.assertTrue(r['stage_evidence']['synthetic_native_2_english_3_arabic_pngs'])
        self.assertFalse(r['stage_evidence']['same_input_full_native_pngs'])
        self.assertFalse(r['full_system_metric_deltas_allowed'])
        self.assertEqual(r['status'],'HOLD_FULL_SYSTEM_COMPARISON')
        self.assertFalse(r['can_release'])
    def test_parser_fail_does_not_invent_success(self):
        c,n,p=fixture();c['status']='HOLD';c['parity_all']=False
        r=assess_full_shadow(c,n,p)
        self.assertFalse(r['stage_evidence']['live_exact_input_v1_v2_parsers'])
        self.assertFalse(r['source_input_only_matched_at_parser'])
    def test_enabled_send_packet_rejected(self):
        c,n,p=fixture();p['arabic']['can_send']=True
        with self.assertRaises(ValueError):assess_full_shadow(c,n,p)
    def test_wrong_discord_destination_rejected(self):
        c,n,p=fixture();p['english']['destination_key']='discord_webhook_arabic'
        with self.assertRaises(ValueError):assess_full_shadow(c,n,p)
    def test_page_hash_mismatch_rejected(self):
        c,n,p=fixture();p['english']['attachments'][0]['sha256']='c'*64
        with self.assertRaises(ValueError):assess_full_shadow(c,n,p)
    def test_wrong_page_count_rejected(self):
        c,n,p=fixture();n['pages'].pop()
        with self.assertRaises(ValueError):assess_full_shadow(c,n,p)
    def test_forged_model_call_rejected(self):
        c,n,p=fixture();n['llm_called']=True
        with self.assertRaises(ValueError):assess_full_shadow(c,n,p)
    def test_bogus_capture_schema_rejected(self):
        c,n,p=fixture();c['schema']='bogus'
        with self.assertRaises(ValueError):assess_full_shadow(c,n,p)
if __name__=='__main__':unittest.main()
