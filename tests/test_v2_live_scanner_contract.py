import unittest
from v2_live_scanner_contract import classify_scanner_response

class ScannerContractTests(unittest.TestCase):
    def test_macro_partial_is_not_falsely_complete(self):
        data={'totalCount':4,'data':[{'s':'TVC:DXY','d':['Dollar',0.13,101.75]},{'s':'COMEX:GC1!','d':['Gold',-1.29,4007.9]}]}
        result=classify_scanner_response(data,requested=['TVC:DXY','COMEX:GC1!','NYMEX:CL1!'],kind='macro',observed_at='2026-10-24T07:13:06+04:00')
        self.assertEqual(result['status'],'partial')
        self.assertEqual(result['missing_symbols'],['NYMEX:CL1!'])
        self.assertFalse(result['publisher_timestamp_verified'])
        self.assertFalse(result['publishable'])
    def test_null_stock_change_does_not_zero_fill(self):
        row={'s':'NASDAQ:NVDA','d':[None,'NVIDIA','Tech',5e12,None,.8,50000000,True,-.59,210.96,'stock']}
        out=classify_scanner_response({'totalCount':1,'data':[row]},requested=['NASDAQ:NVDA'],kind='stocks',observed_at='2026-10-24T07:13:06+04:00')
        self.assertIsNone(out['observations'][0]['change_percent'])
        self.assertEqual(out['observations'][0]['change'], -.59)
        self.assertFalse(out['publishable'])
    def test_nan_rejected(self):
        with self.assertRaises(ValueError):
            classify_scanner_response({'totalCount':1,'data':[{'s':'TVC:DXY','d':['DXY',.1,float('nan')]}]},requested=['TVC:DXY'],kind='macro',observed_at='2026-10-24T07:13:06+04:00')
    def test_malformed_data_refused(self):
        with self.assertRaises(ValueError):
            classify_scanner_response({'totalCount':1,'data':[{'s':'ABC','d':[1]}]},requested=['ABC'],kind='macro',observed_at='2026-10-24T07:13:06+04:00')
    def test_unknown_symbol_not_promoted(self):
        with self.assertRaises(ValueError):
            classify_scanner_response({'totalCount':1,'data':[{'s':'UNEXPECTED','d':['Name',0,1]}]},requested=['TVC:DXY'],kind='macro',observed_at='2026-10-24T07:13:06+04:00')
