import unittest
from v2_b44_staged_registry import candidates,coverage
from v2_b11_coverage_readiness import TARGET_REGIONS

def case():
    reg={'schema_version':'2.0.0-preview','sources':[{'id':'ar-s056'}],
         'staged_sources':[{'id':'candidate-'+str(i),'region':'somalia','language':'en',
            'entrypoint':'https://example.org/'+str(i),'publisher_family_candidate':str(i),
            'enabled':False,'eligible_for_collection':False,'eligible_for_publishing':False,
            'activation_approved':False,'translation_verified':False} for i in range(4)]}
    aud={'regions':{k:{'compatible':1 if k=='somalia' else 3} for k in TARGET_REGIONS}}
    obs=[{'candidate_id':'candidate-'+str(i),'production_compatible':True,
          'collector_status':'active','recent_72h':3} for i in range(4)]
    return reg,aud,obs

class TestB44(unittest.TestCase):
    def test_four_staged_but_record_of_truth_unchanged(self):
        r,_,_=case();self.assertEqual(len(candidates(r)),4);self.assertEqual(len(r['sources']),1)
    def test_hypothetical_does_not_close_production(self):
        r,a,o=case();v=coverage(r,a,o)
        self.assertEqual(v['live_candidate_technical_families'],4)
        self.assertIn('somalia',v['production_regions_below_floor'])
        self.assertFalse(v['regions']['somalia']['production_floor_closed_by_b44'])
        self.assertFalse(v['can_release'])
    def test_explicit_activation_refused(self):
        r,_,_=case();r['staged_sources'][0]['eligible_for_collection']=True
        with self.assertRaises(ValueError):candidates(r)
    def test_same_family_not_independent(self):
        r,_,_=case();r['staged_sources'][1]['publisher_family_candidate']='0'
        with self.assertRaises(ValueError):candidates(r)
    def test_missing_live_candidate_rejected(self):
        r,a,o=case()
        with self.assertRaises(ValueError):coverage(r,a,o[1:])
if __name__=='__main__':unittest.main()
