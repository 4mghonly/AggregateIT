"""Offline rendering regression tests. Fixtures are synthetic, not live data."""
import os
import tempfile
import unittest
from gazette_render import Page, render_p1, render_p2, LAYOUT_AUDIT, pct

def fixture():
    events=[{'title':'European carmakers warn that proposed tariffs could affect production and international trade.',
             'source':'Example financial news source', 'severity':'Medium'} for _ in range(12)]
    types=[('index',['S&P 500','Nasdaq 100','Dow Jones','Russell 2000','VIX']),
           ('index_future',['S&P futures','Nasdaq futures','Dow futures']),
           ('commodity',['Gold','Silver','WTI Crude','Copper']),
           ('forex',['EUR/USD','GBP/USD','USD/JPY','USD/CNH','AUD/USD']),
           ('bond',['US 2Y Yield','US 5Y Yield','US 10Y Yield','US 30Y Yield'])]
    macro={'instruments':[{'name':n,'type':t,'price':4.8 if t=='bond' else 1234.56,'pct':1.23} for t,ns in types for n in ns]}
    pulse={'mega_caps':[{'t':n,'pct':v} for n,v in [('NVDA',2.1),('AAPL',.4),('GOOG',1.3),('MSFT',-1.2),('AMZN',3.5),('AVGO',2.3),('META',-2.4),('TSLA',4.8),('MU',5.2),('LLY',-.5)]],
           'gainers':[{'t':'AAA','pct':391.6},{'t':'BBB','pct':221.3}],
           'losers':[{'t':'CCC','pct':-71.9},{'t':'DDD','pct':-51.3}],
           'hour_movers':[{'t':'NVDA','hour_chg':1.8,'pct':2.6}]*5}
    d={'events':events,'geo_events':events,'pulse':pulse,'macro':macro,'sources_active':['example']*15,
       'social_pulse':{'coverage':{'reddit':0,'twitter':0,'rsshub':4,'stocktwits':0,'blogs':6},
                       'top':[{'t':e['title'],'src':'Institutional blog'} for e in events]},
       'curve_pts':{'2Y':4.68,'5Y':4.8,'10Y':4.95,'30Y':5.3},
       'regime':{'vix':'normal (15–20)','curve_2s10s':'+26.4bp','dxy':'neutral'},'themes':{'Markets':22,'Crypto':37}}
    a={k:'Markets and geopolitical developments require separate assessment. The available observations do not establish a causal link between the headlines and price changes.' for k in ['lead','geopol_read','market_read','social_read','delta','cross_asset','outlook','key_risk']}
    a['headline']='Global markets advance as investors assess geopolitical risks and new economic signals'
    return d,a

class LayoutTests(unittest.TestCase):
    def test_long_text_is_not_cut(self):
        import matplotlib.pyplot as plt
        p=Page('Test',1); b=p.card(.03,.9,.3,.3,'LONG TEXT')
        text='A very long but complete headline with sufficient space to wrap across multiple lines.'
        self.assertTrue(b.add(text))
        self.assertEqual(' '.join(p.wrap(text,b.w,12)),text)
        self.assertFalse(b.add(text*100))
        plt.close(p.fig)

    def test_missing_is_not_zero(self):
        self.assertEqual(pct(None),'Unavailable')
        self.assertEqual(pct(0),'+0.00%')

    def test_full_and_empty_pages(self):
        d,a=fixture()
        with tempfile.TemporaryDirectory() as tmp:
            for data in [d,{}]:
                for i,render in enumerate([render_p1,render_p2]):
                    path=os.path.join(tmp,'page%d.png'%i)
                    render(data,a,True,path)
                    self.assertGreater(os.path.getsize(path),10000)
        self.assertTrue(all(bottom<=end<=top for top,end,bottom in LAYOUT_AUDIT))

if __name__=='__main__':
    unittest.main()
