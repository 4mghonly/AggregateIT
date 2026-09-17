"""Offline Gazette QA. All fixtures are synthetic; no collection or delivery."""
import copy
import os
import time
import unittest
from pathlib import Path
from unittest.mock import patch
import matplotlib.pyplot as plt
from PIL import Image
import gazette_render as g

class Store:
    def get_claim_count(self, event_id): return 1

def fixture():
    now = time.time()
    events = [{"event_id": str(i), "title": title, "severity": "High" if i < 2 else "Medium",
               "status": "NEW", "confidence": 70, "source": "Example News",
               "source_count": 2, "ts": now-600*(i+1), "tickers": ["NVDA"] if i<3 else ["XOM"],
               "sentiment": ["bullish","neutral","bearish"][i%3]}
              for i,title in enumerate([
                  "Shipping companies review regional transport routes",
                  "Central bank publishes its latest policy statement",
                  "Technology companies release quarterly results",
                  "Energy producers update their production outlook",
                  "Trade officials announce a scheduled consultation",
                  "Manufacturers publish new business survey results",
                  "Investors assess the latest inflation release",
                  "Regional authorities issue a transport update"])]
    instruments = [
        ("S&P 500","index",6200,1.0),("Nasdaq 100","index",21000,1.2),
        ("Dow Jones","index",42000,.3),("Russell 2000","index",2100,-.2),
        ("VIX","index",16.2,-3.0),("S&P futures","index_future",6210,.4),
        ("Nasdaq futures","index_future",21050,.5),("Dow futures","index_future",42010,.1),
        ("Gold","commodity",2500,.4),("Silver","commodity",30,.8),
        ("WTI Crude","commodity",70,-.7),("Copper","commodity",4.2,.5),
        ("EUR/USD","forex",1.1,.2),("GBP/USD","forex",1.3,-.2),
        ("USD/JPY","forex",145,.1),("USD/CNH","forex",7.1,.1),("US Dollar Index","forex",99,-.2),
        ("US 2Y Yield","bond",4.1,-.1),("US 5Y Yield","bond",4.2,-.2),
        ("US 10Y Yield","bond",4.3,-.1),("US 30Y Yield","bond",4.5,-.1)]
    d={"sample":True,"store":Store(),"events":events,"geo_events":events[:4],"headlines":events,
       "sources_active":["Example News","Example Wire"],"event_window_h":24,
       "pulse":{"valid":True,"updated":now-120,"session_open":True,
                "mega_caps":[{"t":t,"pct":p} for t,p in [("NVDA",2.6),("AAPL",.3),("GOOG",1.2),("MSFT",1.8),("AMZN",2.6),("AVGO",3.1),("META",-.4),("TSLA",3.6),("MU",1.1),("LLY",-.2),("BRK.B",.1),("JPM",-.5)]],
                "gainers":[{"t":"AAA","pct":12.5}],"losers":[{"t":"BBB","pct":-8.2}],
                "hour_movers":[{"t":"NVDA","hour_chg":1.2,"pct":2.6,"mcap":3e12}],
                "sig":{"AAA":{"pct":12.5,"relvol":4.0},"BBB":{"pct":-8.2,"relvol":2.0}},
                "deltas":{"AAA":1.0,"BBB":-1.0,"CCC":0.0}},
       "macro":{"valid":True,"updated":now-180,"instruments":[{"name":n,"type":t,"price":p,"pct":c} for n,t,p,c in instruments]},
       "regime":{"vix":"normal (15-20)","curve_2s10s":"+20bp","dxy":"neutral"},
       "sector_tape":[("Technology",2.0),("Energy",-.7),("Financials",.3),("Healthcare",-.2)],
       "curve_pts":{"2Y":4.1,"5Y":4.2,"10Y":4.3,"30Y":4.5},"yield_hist":[],
       "themes":{"GG":3,"ME":2,"US":3},"st_radar":[],"reddit":{},
       "social_pulse":{"ts":now-600,"coverage":{"reddit":0,"twitter":0,"blogs":0},"top":[]},
       "previous_edition":{"event_titles":[events[0]["title"],events[1]["title"]]}}
    a={"headline":"Markets Assess Geopolitical Risk as Technology Shares Advance",
       "lead":"The sample combines reported geopolitical developments with observed market changes. These observations do not establish a causal relationship.",
       "geopol_read":"Shipping and policy developments lead this illustrative watchlist. Source reports require separate verification.",
       "market_read":"The sample shows mixed equity performance and a lower oil price. Sector figures describe only the selected mega-cap sample.",
       "social_read":"Retail sentiment is unavailable in this sample. News ticker mentions below are not social-platform sentiment.",
       "delta":"Compare the leading-title lists with the previous edition. A title entering this list need not represent a new event.",
       "cross_asset":"Equities and commodity prices show different session moves. No causal link is inferred.",
       "outlook":"Watch subsequent verified source updates. No calendar events or price forecasts are inferred from missing data.",
       "key_risk":"Incomplete source coverage may omit material developments."}
    return d,a

class LayoutTests(unittest.TestCase):
    def test_values(self):
        self.assertEqual(g.pct(None),"-")
        self.assertEqual(g.pct(0),"+0.00%")
        self.assertEqual(g.pct(float("nan")),"-")
        self.assertEqual(g.market_cap(3e12),"$3.00T")
    def test_timestamps(self):
        with patch.object(g.time,"time",return_value=2000000000):
            self.assertEqual(g.freshness(2000001000),"future timestamp")
            self.assertEqual(g.freshness(1999999940*1000),"1m old")
            self.assertIn("STALE",g.freshness(1999800000))
    def test_claim_scope(self):
        d,_=fixture()
        self.assertIn("Stored claims (not verified): 8",g.quality(d))
        self.assertIn("first 8 displayed events",g.quality(d))
        self.assertIn("not necessarily new events",g.edition_change(d))
    def test_invalid_snapshot(self):
        d,_=fixture(); d["pulse"]["valid"]=False
        prepared=g.prepare(d)
        self.assertEqual(prepared["pulse"]["mega_caps"],[])
        self.assertTrue(d["pulse"]["mega_caps"])
    def test_measured_width(self):
        fig,ax=plt.subplots()
        text="Very long headline with repeated wide words WWWWWWWWWWW "*8
        for line in g.measured_lines(ax,text,.25,12):
            artist=ax.text(0,0,line,fontsize=12)
            self.assertLessEqual(artist.get_window_extent().width,ax.bbox.width*.25+1)
        plt.close(fig)
    def test_render_full_empty_and_long(self):
        d,a=fixture()
        long_a={k:"A long observation needs careful interpretation and independent verification. "*20 for k in a}
        out=Path(os.environ.get("GAZETTE_QA_OUT","qa-samples")); out.mkdir(exist_ok=True)
        with patch("socket.socket",side_effect=AssertionError("Network prohibited during rendering")):
            for name,data,analysis in [("sample",d,a),("empty",{"sample":True},a),("long",d,long_a)]:
                for i,render in enumerate((g.render_p1,g.render_p2),1):
                    path=out/f"{name}-p{i}.png"
                    render(data,analysis,False,path)
                    with Image.open(path) as im: self.assertEqual(im.size,(3840,2160))
if __name__=="__main__":
    unittest.main()
