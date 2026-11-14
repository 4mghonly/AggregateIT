import json,unittest
from v2_r2_http_transport import make_http_caller
from v2_r2_model_adapter import make_analysis_provider
from v2_product_compiler import compile_daily
class Acceptance(unittest.TestCase):
 def test_model_response_reaches_held_english_edition(self):
  class Response:
   status_code=200
   content=b''
   def __init__(self):
    answer={"items":[{"event_id":"ev-1","assessment":"The announcement describes a proposal, not a completed action.","confidence":"low","evidence_excerpt_ids":["ex-1"]}]}
    self.content=json.dumps({"choices":[{"finish_reason":"stop","message":{"content":json.dumps(answer)}}]}).encode()
   def json(self):return json.loads(self.content)
   def close(self):pass
  def transport(url,**kwargs):
   self.assertEqual(kwargs["json"]["model"],"acceptance-model")
   return Response()
  caller=make_http_caller(base_url="https://models.example.org/v1",model="acceptance-model",api_key="test-token",transport=transport)
  provider=make_analysis_provider(caller=caller)
  item={"event_id":"ev-1","region":"gcc","topic":"geopolitics","reporting_status":"publisher_attributed_not_independently_verified","evidence":{"excerpt_id":"ex-1","source_id":"en-001","quote":"Officials announced a proposal.","source_url":"https://www.bbc.com/news/example","original_language":"en"}}
  plan={"schema":"aggregateit-editorial-plan/1","product":"english","language":"en","slot_id":"2026-11-14T12:00:00+00:00","delivery_authorized":False,"items":[item]}
  candidates=provider(product="english",items=[item],as_of=plan["slot_id"])
  result=compile_daily(editorial_plan=plan,analysis_candidates=candidates)
  self.assertEqual(result["stories"][0]["analysis_status"],"evidence_referenced_unverified")
  self.assertIn("proposal",result["stories"][0]["assessment"])
  self.assertFalse(result["delivery_authorized"])
  self.assertFalse(result["content_truth_verified"])
if __name__=="__main__":unittest.main()
