"""No-post validation of live TradingView scanner responses.

Request-time is never presented as an exchange quote timestamp. Missing
instruments and null measurements remain unavailable, not zero.
"""
from __future__ import annotations
from datetime import datetime
from math import isfinite

STOCK_COLS=("ticker","description","sector","market_cap_calc","change_percent","relative_volume_10d_calc","volume","is_primary","change","close","type")
MACRO_COLS=("description","change","close")

def _measure(value):
    if value is None:return None
    if isinstance(value,bool) or not isinstance(value,(int,float)) or not isfinite(value):
        raise ValueError('invalid_scanner_measurement')
    return value

def classify_scanner_response(response:dict,*,requested:list[str],kind:str,observed_at:str)->dict:
    if kind not in ('macro','stocks') or not isinstance(response,dict):
        raise ValueError('invalid_scanner_response')
    try:
        moment=datetime.fromisoformat(observed_at.replace('Z','+00:00'))
    except (ValueError,TypeError,AttributeError) as exc:
        raise ValueError('invalid_observed_at') from exc
    if moment.utcoffset() is None:raise ValueError('invalid_observed_at')
    if (not isinstance(requested,list) or not 1<=len(requested)<=50
            or any(not isinstance(x,str) or not x for x in requested)
            or len(set(requested))!=len(requested)):
        raise ValueError('invalid_requested_symbols')
    rows=response.get('data')
    if (not isinstance(rows,list) or len(rows)>50 or
            type(response.get('totalCount')) is not int):
        raise ValueError('invalid_scanner_response')
    keys=MACRO_COLS if kind=='macro' else STOCK_COLS
    results=[];seen=set()
    for row in rows:
        if (not isinstance(row,dict) or not isinstance(row.get('s'),str)
                or row['s'] not in requested or row['s'] in seen):
            raise ValueError('unexpected_scanner_symbol')
        vals=row.get('d')
        if not isinstance(vals,list) or len(vals)!=len(keys):
            raise ValueError('invalid_scanner_columns')
        record=dict(zip(keys,vals));seen.add(row['s'])
        for field in (('close','change') if kind=='macro'
                      else ('market_cap_calc','change_percent','relative_volume_10d_calc','volume','change','close')):
            record[field]=_measure(record[field])
        results.append({'symbol':row['s'],**record})
    missing=[x for x in requested if x not in seen]
    return {'schema':'aggregateit-v2-tradingview-scanner-observation/1',
            'kind':kind,'observed_at':moment.isoformat(),
            'observations':results,'requested_symbols':requested,
            'missing_symbols':missing,'status':'partial' if missing else 'complete_response',
            'publisher_timestamp_verified':False,'price_accuracy_verified':False,
            'cross_provider_corrob_verified':False,'publishable':False}
