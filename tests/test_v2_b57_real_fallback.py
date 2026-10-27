"""B57 production failover path with injected primary failure and real route stub."""
import unittest,json
from v2_b57_real_fallback import evaluate,_row,CAP,PRIOR_B56_RESERVED

class Fake:
    status_code=200;content=b'{}'
    def __init__(self,input):self.input=input
    def json(self):
        return {'usage':{'cost':.0003},
          'choices':[{'finish_reason':'stop','message':{'content':json.dumps(
             {'items':[{'index':0,
                'title_ar':'اقترح مسؤولون في الصومال 12 عيادة يوم 27 أكتوبر',
                'summary_ar':'لم تتم الموافقة على الخطة ولم تفتح أي عيادة.'}]},ensure_ascii=False)}}]}
    def close(self):pass
def send(url,*,headers,json,timeout,allow_redirects):
    return Fake(__import__('json').loads(json['messages'][1]['content']))
class Checks(unittest.TestCase):
    def test_real_production_controller_uses_fallback_under_injected_primary_failure(self):
        x=evaluate(api_key='fixture-key',transport=send)
        self.assertEqual(x['actual_fallback_calls'],2)
        self.assertTrue(all(t['structural_pass'] for t in x['records']))
        self.assertTrue(all(t['production_controller_selected_fallback'] for t in x['records']))
        self.assertLess(x['cumulative_reserved_usd'],CAP)
        self.assertEqual(x['cumulative_reported_usd'],.0029537)
        self.assertFalse(x['live_full_production_fallback_verified'])
        self.assertFalse(x['can_release'])
    def test_missing_secret_makes_no_network_calls(self):
        x=evaluate(api_key='',transport=lambda *a,**k:self.fail('network'))
        self.assertEqual(x['actual_fallback_calls'],0)
    def test_forbidden_language(self):
        with self.assertRaises(ValueError):_row('fa')
    def test_budget_remaining(self):
        self.assertGreater(CAP-PRIOR_B56_RESERVED,.3)
if __name__=='__main__':unittest.main()
