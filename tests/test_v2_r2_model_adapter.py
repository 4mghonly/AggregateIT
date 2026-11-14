import unittest
from v2_r2_model_adapter import parse_analysis_response,make_analysis_provider
class ModelAdapterTests(unittest.TestCase):
 def setUp(self):
  self.items=[{"event_id":"ev1","evidence":{"excerpt_id":"ex1","quote":"Officials announced a proposal."}}]
 def test_valid_json_candidate(self):
  def caller(system,payload):
   return '{"items":[{"event_id":"ev1","assessment":"The proposal is not a confirmed outcome.","confidence":"low","evidence_excerpt_ids":["ex1"]}]}'
  result=make_analysis_provider(caller=caller)(product="english",items=self.items,as_of="2026-11-14T12:00:00+00:00")
  self.assertEqual(result[0]["event_id"],"ev1")
 def test_hallucinated_evidence_is_rejected(self):
  with self.assertRaisesRegex(ValueError,"untrusted_analysis_evidence"):
   parse_analysis_response('{"items":[{"event_id":"ev1","assessment":"Invented","confidence":"high","evidence_excerpt_ids":["fake"]}]}',self.items)
 def test_unknown_event_is_rejected(self):
  with self.assertRaisesRegex(ValueError,"untrusted_analysis_event"):
   parse_analysis_response('{"items":[{"event_id":"other","assessment":"Invented","confidence":"high","evidence_excerpt_ids":["ex1"]}]}',self.items)
 def test_missing_caller_abstains_without_network(self):
  self.assertEqual(make_analysis_provider()(product="english",items=self.items,as_of="2026-11-14T12:00:00+00:00"),[])
if __name__=="__main__":unittest.main()
