"""Real V1 TradingView cache -> evidence-labelled V2 English market context."""
import unittest
from datetime import datetime,timezone
from v2_market_bridge import convert_v1_market_pulse
from v2_b46_live_editorial import compile_captured_articles
from test_v2_b46_live_editorial import en, NOW, SLOT

class ReplacementMarketTests(unittest.TestCase):
 def test_valid_fresh_v1_cache_passes_into_english_editorial(self):
  t=datetime.fromisoformat(NOW).timestamp()
  pulse={"valid":True,"updated":t-300,"session_open":False,
         "mega_caps":[{"t":"AAPL","price":222.25,"pct":0.8},{"t":"MSFT","price":400.5,"pct":-0.6}]}
  markets=convert_v1_market_pulse(pulse,as_of=NOW)
  self.assertEqual([x["symbol"] for x in markets],["AAPL","MSFT"])
  self.assertEqual(markets[0]["source"],"tradingview_cached_snapshot")
  r=compile_captured_articles([en()],as_of=NOW,slot_id=SLOT,market_observations=markets)
  self.assertEqual(r["products"]["english"]["newsroom"]["market_data_status"],"observed_unverified")
  self.assertEqual(len(r["products"]["english"]["newsroom"]["market_observations"]),2)
  self.assertEqual(r["products"]["arabic"]["newsroom"]["market_observations"],[])
  self.assertFalse(r["can_send"])
 def test_stale_invalid_or_future_cached_data_never_promoted(self):
  t=datetime.fromisoformat(NOW).timestamp()
  sample={"valid":True,"updated":t-86400,"mega_caps":[{"t":"AAPL","price":200}]}
  self.assertEqual(convert_v1_market_pulse(sample,as_of=NOW),[])
  sample["updated"]=t+1000
  self.assertEqual(convert_v1_market_pulse(sample,as_of=NOW),[])
  sample["updated"]=t;sample["valid"]=False
  self.assertEqual(convert_v1_market_pulse(sample,as_of=NOW),[])
 def test_no_unattributed_market_symbols_or_prices(self):
  t=datetime.fromisoformat(NOW).timestamp()
  sample={"valid":True,"updated":t,"mega_caps":[{"t":"BAD LINK","price":123},{"t":"AAPL","price":float("nan")},{"t":"MSFT","price":None}]}
  self.assertEqual(convert_v1_market_pulse(sample,as_of=NOW),[])
if __name__=="__main__":unittest.main()
