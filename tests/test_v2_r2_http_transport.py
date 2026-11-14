import json,unittest
from v2_r2_http_transport import make_http_caller
class HttpTransportTests(unittest.TestCase):
 def test_missing_credentials_abstains(self):
  self.assertIsNone(make_http_caller(base_url="https://api.example.com/v1",model="test",api_key=""))
 def test_rejects_insecure_url(self):
  with self.assertRaisesRegex(ValueError,"invalid_model_endpoint"):
   make_http_caller(base_url="http://api.example.com/v1",model="test",api_key="secret")
 def test_extracts_structured_completion(self):
  seen=[]
  class Response:
   status_code=200
   content=b'{"choices":[{"message":{"content":"{\\"items\\":[]}"}}]}'
   def json(self):return json.loads(self.content)
   def close(self):pass
  def post(url,**kwargs):
   seen.append((url,kwargs))
   return Response()
  caller=make_http_caller(base_url="https://api.example.com/v1",model="test",api_key="secret",transport=post)
  self.assertEqual(caller("system","{}"),'{"items":[]}')
  self.assertEqual(seen[0][1]["timeout"],(7,35))
  self.assertFalse(seen[0][1]["allow_redirects"])
 def test_disallows_embedded_credentials(self):
  with self.assertRaisesRegex(ValueError,"invalid_model_endpoint"):
   make_http_caller(base_url="https://user:pass@api.example.com/v1",model="test",api_key="secret")
if __name__=="__main__":unittest.main()
