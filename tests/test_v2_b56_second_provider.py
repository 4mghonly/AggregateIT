"""B56 one new fallback-family experiment without repetition or cap inflation."""
import unittest,json
from v2_b56_second_provider import CAP,PRIOR_B55_RESERVED,run,reserve,parse
from v2_b55_budgeted_models import make_fixture
class Reply:
    status_code=200;content=b'{}'
    def __init__(self,u):self.u=u
    def json(self):
        d={'items':[{'index':0,'source_sha256':self.u['source_sha256'],
           'title_ar':'اقترح مسؤولون 12 عيادة في الصومال يوم 27 أكتوبر',
           'summary_ar':'لم يتم اعتماد الخطة ولم يُعلن افتتاح أي عيادة.'}]}
        return {'choices':[{'finish_reason':'stop','message':{'content':json.dumps(d,ensure_ascii=False)}}],
                'usage':{'cost':.0004}}
    def close(self):pass
def send(url,*,headers,json,timeout,allow_redirects):
    return Reply(__import__('json').loads(json['messages'][1]['content']))
class Checks(unittest.TestCase):
    def test_full_four_calls_and_cumulative_cost(self):
        x=run(key='test',sender=send)
        self.assertEqual(x['attempts'],4)
        self.assertEqual(x['combined_reported_usd'],.0029859)
        self.assertLess(x['combined_conservative_reserved_usd'],CAP)
        self.assertFalse(x['can_release'])
    def test_invalid_models_and_duplicate_scenario_fail(self):
        with self.assertRaises(ValueError):run(key='test',sender=send,scenarios=[('unknown','en')])
        with self.assertRaises(ValueError):run(key='test',sender=send,scenarios=[('fallback','en')]*2)
    def test_no_key_no_network(self):
        x=run(key='',sender=lambda *a,**kw:self.fail('network'))
        self.assertEqual(x['attempts'],0)
    def test_explicit_fence_and_truncation_handled(self):
        source=make_fixture('en')
        raw=Reply({'source_sha256':source['source_sha256']}).json()
        fence=chr(96)*3
        raw['choices'][0]['message']['content']=fence+'json\n'+raw['choices'][0]['message']['content']+'\n'+fence
        self.assertTrue(parse(raw,source)['structural_pass'])
        raw['choices'][0]['finish_reason']='length'
        with self.assertRaisesRegex(ValueError,'truncated'):parse(raw,source)
    def test_bound(self):
        self.assertEqual(round(CAP-PRIOR_B55_RESERVED,7),.4676852)
        self.assertLess(reserve('x'*2000,'fallback'),.05)
if __name__=='__main__':unittest.main()
