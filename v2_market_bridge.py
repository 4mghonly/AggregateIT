"""Read-only adapter from V1's canonical TradingView pulse into V2 English editions.

Reuses the V1 market refresh and data cache. No new market query, API key,
provider selection or unsupported market unit assumption. Explicitly stale
or untrustworthy observations are omitted, not fabricated.
"""
from __future__ import annotations
from datetime import datetime,timezone
from math import isfinite
import re

SYMBOL=re.compile(r"^[A-Z][A-Z0-9.\\-]{0,10}$")
MAX_AGE_SECONDS=20*3600

def convert_v1_market_pulse(pulse:dict|None,*,as_of:str,max_items:int=8)->list[dict]:
 if not isinstance(pulse,dict) or pulse.get("valid") is not True:return []
 if type(max_items) is not int or not 1<=max_items<=12:raise ValueError("invalid_market_item_budget")
 try:
  stamp=datetime.fromisoformat(as_of.replace("Z","+00:00"))
  if stamp.utcoffset() is None:raise ValueError("naive_market_slot")
  now=stamp.timestamp()
 except (TypeError,AttributeError,ValueError) as exc:raise ValueError("invalid_market_slot") from exc
 updated=pulse.get("updated")
 if not isinstance(updated,(float,int)) or isinstance(updated,bool) or not isfinite(updated):return []
 if not -300<=now-updated<=MAX_AGE_SECONDS:return []
 rows=pulse.get("mega_caps")
 if not isinstance(rows,list):return []
 observed=datetime.fromtimestamp(updated,timezone.utc).isoformat()
 result=[];seen=set()
 for item in rows[:60]:
  if not isinstance(item,dict):continue
  sym=item.get("t")
  value=item.get("price")
  if not isinstance(sym,str) or not SYMBOL.fullmatch(sym) or sym in seen:continue
  if not isinstance(value,(float,int)) or isinstance(value,bool) or not isfinite(value) or value<=0:continue
  seen.add(sym)
  result.append({"source":"tradingview_cached_snapshot","symbol":sym,
                 "observed_at":observed,"value":float(value),
                 "unit":"quoted_price_currency_unspecified",
                 "status":"previous_session" if pulse.get("session_open") is False else "session_snapshot"})
  if len(result)>=max_items:break
 return result
