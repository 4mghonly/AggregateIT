import unittest
from v2_b109_b111_evidence import classify_translation_failure,partial_shadow_receipt

class EvidenceTests(unittest.TestCase):
 def test_403_is_access_hold(self):
  x=classify_translation_failure(403,primary_attempted=True,fallback_attempted=True)
  self.assertEqual(x['category'],'AUTH_OR_PROVIDER_ACCESS')
  self.assertFalse(x['credential_validity_verified'])
 def test_429_is_rate_limit(self):
  self.assertEqual(classify_translation_failure(429,primary_attempted=True,fallback_attempted=False)['category'],'RATE_LIMIT')
 def test_missing_bilingual_rows_hold(self):
  with self.assertRaises(ValueError):
   partial_shadow_receipt({'schema':'aggregateit-v2-b49-single-slot-preflight/1','can_release':False,'rows':[]},capture_date='2026-10-30')

if __name__=='__main__':unittest.main()
