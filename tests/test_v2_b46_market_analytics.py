"""B46 market observation and Naysayer abstention are non-publishable."""
import unittest
from v2_b46_market_analytics import assess_market_observation,audit_critic_abstention
from v2_b46_live_editorial import compile_captured_articles
NOW="2026-10-27T08:00:00+00:00"
SLOT="2026-10-27T12:00:00+04:00"

class MarketAndNaysayerTests(unittest.TestCase):
    def test_real_scanner_shape_is_observation_not_verified_financial_quote(self):
        data={"totalCount":2,"data":[{"s":"TVC:DXY","d":["Dollar",0.2,105.6]},
                                       {"s":"COMEX:GC1!","d":["Gold",None,4035.0]}]}
        result=assess_market_observation(data,observed_at=NOW)
        self.assertEqual(result["received_count"],2)
        self.assertEqual(result["missing_symbols"],["NYMEX:CL1!"])
        self.assertEqual(result["close_measurements_available"],2)
        self.assertFalse(result["exchange_quote_timestamp_verified"])
        self.assertFalse(result["market_data_can_enter_edition"])
        self.assertFalse(result["rights_for_republication_verified"])
    def test_null_close_not_counted_or_turned_to_zero(self):
        data={"totalCount":1,"data":[{"s":"TVC:DXY","d":["DXY",None,None]}]}
        result=assess_market_observation(data,observed_at=NOW,requested=["TVC:DXY"])
        self.assertEqual(result["close_measurements_available"],0)
        self.assertFalse(result["independent_market_price_verified"])
    def test_malformed_scanner_fails_closed(self):
        with self.assertRaises(ValueError):
            assess_market_observation({"totalCount":1,"data":[{"s":"TVC:DXY","d":[1]}]},observed_at=NOW)
    def test_unapproved_stock_or_scanner_symbol_rejected(self):
        with self.assertRaises(ValueError):
            assess_market_observation({"totalCount":0,"data":[]},observed_at=NOW,requested=["NASDAQ:AAPL"])
    def test_english_and_arabic_critics_abstain_without_external_verification(self):
        out=compile_captured_articles([],as_of=NOW,slot_id=SLOT)
        review=audit_critic_abstention(out["products"])
        self.assertEqual(review["products"]["english"]["review_status"],"insufficient_evidence")
        self.assertEqual(review["products"]["arabic"]["review_status"],"insufficient_evidence")
        self.assertFalse(review["editorial_critique_publishable"])
    def test_forged_naysayer_claim_rejected(self):
        out=compile_captured_articles([],as_of=NOW,slot_id=SLOT)
        out["products"]["english"]["critique"]["sections"][0]["review_status"]="supported_challenge"
        with self.assertRaises(ValueError):
            audit_critic_abstention(out["products"])
    def test_any_publishable_critic_is_rejected(self):
        out=compile_captured_articles([],as_of=NOW,slot_id=SLOT)
        out["products"]["arabic"]["no_publication_authority"]=False
        with self.assertRaises(ValueError):
            audit_critic_abstention(out["products"])
if __name__=="__main__":unittest.main()
