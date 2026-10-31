import unittest
from v2_b118_layout_gate import prioritize_uae
class UaeOrder(unittest.TestCase):
 def test_uae_moves_first_without_dropping_others(self):
  rows=[{"subject_country":"YE","event_id":"y"},{"subject_country":"AE","event_id":"u"},{"subject_country":"IR","event_id":"i"}]
  out=prioritize_uae(rows)
  self.assertEqual([x["event_id"] for x in out],["u","y","i"])
  self.assertEqual(rows[0]["event_id"],"y")
 def test_real_brief_orders_uae_first_and_keeps_native_quotes(self):
  from v2_arabic_application_rehearsal import _render_brief
  def item(country,region,event,quote):
   return {'event_id':event,'subject_country':country,'region':region,
           'reporting_status':'publisher_attributed_not_independently_verified',
           'analysis_status':'abstained_unverified',
           'evidence':{'original_language':'ar','quote':quote,'source_id':event,
                       'source_url':'https://example.org/'+event,
                       'source_date':'2026-10-31T08:00:00+00:00'}}
  plan={'product':'arabic','delivery_authorized':False,
        'items':[item('YE','yemen','y','أعلنت جهة عن اجتماع في اليمن.'),
                 item('AE','gcc','u','أعلنت جهة عن اجتماع في الإمارات.')]}
  brief=_render_brief(plan,{'synthetic':True,'slot_id':'2026-10-31T08:00:00+00:00'})
  self.assertEqual([x['fingerprint'] for x in brief['events']],['u','y'])
  self.assertEqual(brief['events'][0]['summary_ar'],'أعلنت جهة عن اجتماع في الإمارات.')
 def test_no_uae_preserves_order(self):
  rows=[{"subject_country":"YE"},{"subject_country":"IR"}]
  self.assertEqual(prioritize_uae(rows),rows)
if __name__=="__main__":unittest.main()
