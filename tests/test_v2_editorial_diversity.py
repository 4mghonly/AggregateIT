import unittest
from v2_editorial import select_diverse_english
class EnglishDiversity(unittest.TestCase):
 def test_relevance_with_source_diversity(self):
  rows=[{"event_id":str(i),"priority":100-i,"region":"gcc","evidence":{"source_id":"a"}} for i in range(5)]
  rows += [{"event_id":"six","priority":94,"region":"iran","evidence":{"source_id":"b"}}]
  chosen=select_diverse_english(rows,3)
  self.assertEqual(len(chosen),3)
  self.assertIn("six",[x["event_id"] for x in chosen])
 def test_no_invented_items(self):
  rows=[{"event_id":"one","priority":99,"region":"gcc","evidence":{"source_id":"a"}}]
  self.assertEqual(select_diverse_english(rows,6),rows)
if __name__=="__main__":unittest.main()
