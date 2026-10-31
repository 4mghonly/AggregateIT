import unittest
from v2_b117_grounded_digest import grounded_digest
class GroundedDigestTests(unittest.TestCase):
 def test_only_uses_admitted_quotes(self):
  items=[{"region":"gcc","evidence":{"quote":"UAE officials announced new security talks.","source_id":"agency-a"}},
         {"region":"yemen","evidence":{"quote":"Yemen officials reported renewed talks.","source_id":"agency-b"}}]
  d=grounded_digest(items,language="en")
  self.assertIn("UAE officials announced new security talks.",d["lead"])
  self.assertIn("Yemen officials reported renewed talks.",d["lead"])
  self.assertNotIn("independently confirmed",d["lead"].lower())
 def test_no_items_abstains(self):
  self.assertEqual(grounded_digest([],language="en")["status"],"insufficient_evidence")
 def test_arabic_uses_native_evidence(self):
  d=grounded_digest([{"region":"gcc","evidence":{"quote":"أعلنت الجهات إجراء محادثات أمنية جديدة.","source_id":"x"}}],language="ar")
  self.assertIn("أعلنت",d["lead"])
if __name__=="__main__":unittest.main()
