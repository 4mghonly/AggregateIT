import unittest,json
from pathlib import Path
from v2_b58_model_release_gate import assess_selection

def config():
    return json.loads(Path('config/v2/b58_staged_paid_models.json').read_text())
class TestB58(unittest.TestCase):
    def test_model_names_and_budget_staged_disabled(self):
        r=assess_selection(config())
        self.assertEqual(r['model_primary_staged'],'google/gemini-3.1-flash-lite')
        self.assertEqual(r['model_fallback_staged'],'openai/gpt-oss-120b')
        self.assertGreater(len(r['unresolved']),9)
        self.assertFalse(r['can_release'])
    def test_caller_supplied_same_slot_cannot_fake_release(self):
        r=assess_selection(config(),recorded_full_v1_v2_match=True)
        self.assertIn('v1_v2_same_slot_full_edition_quality_not_verified',r['unresolved'])
    def test_production_enablement_refused(self):
        c=config();c['activation']['enabled']=True
        with self.assertRaises(ValueError):assess_selection(c)
    def test_false_budget_or_model_refused(self):
        c=config();c['budget']['approved_usd']=500
        with self.assertRaises(ValueError):assess_selection(c)
        c=config();c['fallback']['model']='qwen/qwen3.8-flash'
        with self.assertRaises(ValueError):assess_selection(c)
if __name__=='__main__':unittest.main()
