import unittest
from v2_b45_named_free_candidate import MODEL,evaluate_named_free
from v2_b45_free_live_models import fixture

def route(model='openrouter/free'):
    return {'base':'https://openrouter.ai/api/v1','chat':'/chat/completions',
            'model':model,'key':'dummy_key','options':{}}
def output(r,s,p,max_tokens):
    self_item=p['items'][0]
    return {'items':[{'index':0,'source_sha256':self_item['source_sha256'],
      'title_ar':'ناقش مسؤولو الصومال خطة 12 مركزاً يوم 27 أكتوبر',
      'summary_ar':'لم يتم تأكيد الافتتاح، وكانت هذه مجرد خطة.'}]}
class NamedFree(unittest.TestCase):
    def test_pinned_explicit_free_model(self):
        self.assertEqual(MODEL,'nvidia/nemotron-3.5-lightning:free')
    def test_two_synthetic_language_calls_are_not_prod_failover(self):
        r=evaluate_named_free(configured=route(),caller=output,resolve_env=False)
        self.assertEqual(r['attempts'],2)
        self.assertEqual(r['languages'],{'en':'STRUCTURAL_PASS','so':'STRUCTURAL_PASS'})
        self.assertFalse(r['actual_second_provider_verified'])
        self.assertFalse(r['can_release'])
    def test_nonfree_or_missing_primary_credential_refused(self):
        for bad in ({},route(model='glm-5.3')):
            r=evaluate_named_free(configured=bad,caller=lambda *a,**k:self.fail('network'),resolve_env=False)
            self.assertEqual(r['attempts'],0)
    def test_invalid_json_or_wrong_figures_hold(self):
        def wrong(r,s,p,max_tokens):
            result=output(r,s,p,max_tokens)
            result['items'][0]['title_ar']='فتح 13 مركزاً يوم 27 أكتوبر'
            return result
        r=evaluate_named_free(configured=route(),caller=wrong,resolve_env=False)
        self.assertEqual(r['status'],'HOLD_INCOMPLETE_FREE_MODEL_QUALITY')
if __name__=='__main__':unittest.main()
