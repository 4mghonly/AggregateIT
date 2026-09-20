"""calibrate.py — weekly event/market association diagnostic.

This is intentionally NOT a historical prediction hit-rate calculator: the current
runtime retains only the latest mover snapshot, not the market snapshot that followed
each event. The report therefore measures whether recent event ticker signals overlap
the current mover set and labels that limitation explicitly.
"""
import os, json, time, re
from storage import SQLiteStore
import market

BASE = os.path.dirname(os.path.abspath(__file__))
REPORTS = os.path.join(BASE, "reports")
CAL_FILE = os.path.join(REPORTS, "calibration_report.json")

def event_tickers(event, known=None):
    """Extract canonical ticker-like signals from entity, triggers and title.

    When a known ticker universe is supplied, only members of that universe are
    returned. This prevents geopolitical entities or keyword IDs being counted
    as securities.
    """
    known={str(x).upper() for x in (known or [])}
    found=set()
    def add(raw):
        token=str(raw or "").strip().upper().lstrip("$")
        if re.fullmatch(r"[A-Z][A-Z0-9.]{0,5}",token):
            if not known or token in known:
                found.add(token)
    add(event.get("entity"))
    try:
        triggers=json.loads(event.get("triggers_json") or "[]")
    except (ValueError,TypeError):
        triggers=[]
    if not isinstance(triggers,list):
        triggers=[]
    for trigger in triggers:
        text=str(trigger or "").strip().upper()
        match=re.match(r"^\$?([A-Z][A-Z0-9.]{0,5})(?=\s|\(|$)",text)
        if match:
            add(match.group(1))
    if known:
        for token in re.findall(r"\$?([A-Z][A-Z0-9.]{0,5})\b",str(event.get("title") or "").upper()):
            if token in known:
                found.add(token)
    return found

def build_report(store=None,pulse=None):
    store=store or SQLiteStore()
    pulse=pulse if pulse is not None else (market.load_market_pulse() or {})
    sig_movers={str(x).upper() for x in (pulse.get("sig") or {}).keys()}
    hour_movers={str(m.get("t","")).upper() for m in pulse.get("hour_movers",[]) if m.get("t")}
    active_tickers=sig_movers | hour_movers
    events=store.recent_all_events(hours=168,limit=500)
    report={
        "ts":time.time(),
        "methodology":"current-snapshot association only; not subsequent-outcome or predictive calibration",
        "total_events":len(events),
        "active_tickers_snapshot":len(active_tickers),
        "market_snapshot_available":bool(active_tickers),
        "by_importance":{},
    }
    for imp in ("Critical","High","Medium","Low"):
        subset=[event for event in events if event.get("severity")==imp]
        with_signal=0
        overlaps=0
        for event in subset:
            tickers=event_tickers(event,active_tickers)
            if tickers:
                with_signal+=1
                if tickers & active_tickers:
                    overlaps+=1
        rate=(overlaps/with_signal*100) if with_signal else 0
        report["by_importance"][imp]={
            "count":len(subset),
            "events_with_current_ticker_signal":with_signal,
            "current_mover_overlap":overlaps,
            "current_mover_overlap_pct":round(rate,1),
        }
    return report

def main():
    report=build_report()
    os.makedirs(REPORTS,exist_ok=True)
    with open(CAL_FILE,"w",encoding="utf-8") as f:
        json.dump(report,f,indent=2)
    print("Calibration diagnostic generated:",CAL_FILE)
    print("Methodology:",report["methodology"])
    for imp,data in report["by_importance"].items():
        print(f"  {imp}: {data['count']} events; {data['current_mover_overlap_pct']}% current-mover overlap among ticker-signalled events")

if __name__=="__main__":
    main()
