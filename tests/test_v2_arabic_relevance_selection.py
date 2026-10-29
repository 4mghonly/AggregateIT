import unittest
from v2_editorial import select_relevance_first

class ArabicSelectionTests(unittest.TestCase):
    def test_non_uae_regions_compete_on_priority_only(self):
        rows=[{'event_id':'a','subject_country':'JO','priority':20,'region':'jordan'}, {'event_id':'b','subject_country':'IR','priority':95,'region':'iran'}, {'event_id':'c','subject_country':'PS','priority':30,'region':'palestine_israel'}, {'event_id':'d','subject_country':'IQ','priority':90,'region':'iraq'}]
        self.assertEqual([x['event_id'] for x in select_relevance_first(rows,2)],['b','d'])
    def test_uae_emphasis_without_suppressing_all_major_other_news(self):
        rows=[{'event_id':'ae','subject_country':'AE','priority':70,'region':'gcc'}, {'event_id':'ir','subject_country':'IR','priority':99,'region':'iran'}, {'event_id':'iq','subject_country':'IQ','priority':95,'region':'iraq'}]
        self.assertEqual([x['event_id'] for x in select_relevance_first(rows,2)],['ae','ir'])

if __name__=='__main__':unittest.main()
