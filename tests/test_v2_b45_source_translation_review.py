import unittest
from v2_b45_source_translation_review import samples_for_source,inspect_translations,pending_summary

def fixture():
    source={'id':'candidate-somali-dispatch','language':'en','enabled':False}
    article={'source_id':source['id'],'language':'en','title':'Somalia delegates meet 27 October',
     'text':'Officials confirmed 12 delegates and 12 observers.',
     'url':'https://example.org/story'}
    return samples_for_source(source,[article])[0]

def proposal(x,summary='أكد مسؤولون حضور 12 مندوباً و12 مراقباً.'):
    return {'index':0,'source_sha256':x['source_sha256'],
            'title_ar':'اجتمع مندوبو الصومال في 27 أكتوبر','summary_ar':summary}

class TestB45(unittest.TestCase):
    def test_source_digest_bound_and_not_publishable(self):
        x=fixture();r=inspect_translations([x],{'items':[proposal(x)]})
        self.assertEqual(r['structural_review_passed'],1)
        self.assertFalse(r['review'][0]['publishable'])
        self.assertFalse(r['semantic_translation_verified'])
    def test_unknown_digest_rejected(self):
        x=fixture();y=proposal(x);y['source_sha256']='f'*64
        self.assertEqual(inspect_translations([x],{'items':[y]})['structural_review_passed'],0)
    def test_repeated_number_mutation_rejected(self):
        x=fixture()
        r=inspect_translations([x],{'items':[proposal(x,'أكد مسؤولون حضور 12 مندوباً و13 مراقباً.')]})
        self.assertEqual(r['structural_review_passed'],0)
    def test_non_arabic_rejected(self):
        x=fixture();y=proposal(x);y['title_ar']='Somalia officials met';y['summary_ar']='12 delegates and 12 observers'
        self.assertEqual(inspect_translations([x],{'items':[y]})['structural_review_passed'],0)
    def test_missing_model_does_not_fabricate_translation(self):
        x=fixture();r=inspect_translations([x],{'items':[]})
        self.assertEqual(r['reasons']['missing_translation'],1)
        self.assertFalse(r['can_release'])
        self.assertNotIn(x['title'],repr(pending_summary([x])))
    def test_disabled_sources_only(self):
        with self.assertRaises(ValueError):samples_for_source({'enabled':True},[])
if __name__=='__main__':unittest.main()
