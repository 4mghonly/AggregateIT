"""slide.py v10 — THE AGGREGATE GAZETTE. 4K two-page editorial deck.
Bordered panels with fixed zones: no overlaps, no dead whitespace.
llm.chat token tracking, claims corroboration, social/OSINT lanes."""
import os, json, re, time, textwrap, requests
from contextlib import ExitStack
from urllib.parse import urlsplit, urlunsplit
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from datetime import datetime, timezone
from llm import chat
from storage import SQLiteStore
import market
from briefing import fetch_stocktwits, load_window, theme_counts, DOMAIN_NAMES

BASE = os.path.dirname(os.path.abspath(__file__))
REPORTS = os.path.join(BASE, "reports")
P1 = os.path.join(REPORTS, "intel_slide_p1.png")
P2 = os.path.join(REPORTS, "intel_slide_p2.png")
PREV_FILE = os.path.join(REPORTS, "prev_slide.json")
YIELD_FILE = os.path.join(market.DATA, "yield_hist.json")

PAPER, INK, MUT2, CARDL = "#F6F1E7", "#1C1B18", "#6E675C", "#D8CFBC"
GEO, MKT, SOC, UP, DN, HI = "#7D2A2A", "#1F3864", "#8A6D1F", "#2E5E3A", "#A33B2E", "#C89B2A"
SEV_COLOR = {"Critical": DN, "High": "#B4622D", "Medium": HI, "Low": MUT2}
GEO_TAGS = {"GG", "ME", "TR", "CY", "US"}

def _clean(s): return re.sub(r'[^\x20-\x7E]', '', s or '').strip()
def _wrap(s, n): return textwrap.wrap(_clean(s), n) or [""]

def _fit(text, width, max_lines):
    lines = textwrap.wrap(_clean(text), width)
    if len(lines) <= max_lines: return lines
    s = " ".join(lines[:max_lines])
    cut = max(s.rfind(". "), s.rfind("! "), s.rfind("? "))
    if cut > len(s) * 0.5: s = s[:cut + 1]
    else: s = s.rstrip() + " ..."
    return textwrap.wrap(s, width)[:max_lines]

_DOLLAR_RE = re.compile(r"\$\s?[\d,]+")
def _scrub(text):
    sents = re.split(r"(?<=[.!?])\s+", _clean(text))
    return " ".join(s for s in sents if not _DOLLAR_RE.search(s))

def _fmt_price(p, t):
    if p is None: return "-"
    if t in ("forex",): return "%.4f" % p
    if t in ("bond",): return "%.2f%%" % p
    if p >= 10000: return "%.0f" % p
    if p >= 100: return "%.1f" % p
    return "%.2f" % p

def _load_prev():
    try:
        with open(PREV_FILE) as f: return json.load(f)
    except Exception: return None

def _save_prev(a, d):
    try:
        with open(PREV_FILE, "w") as f:
            json.dump({"ts": time.time(), "summary": a.get("lead", ""),
                       "event_titles": [e.get("title", "") for e in d["events"][:8]],
                       "regime": d.get("regime", {}),
                       "top_gainer": d["pulse"].get("gainers", [{}])[0].get("t") if d["pulse"].get("gainers") else None,
                       "top_loser": d["pulse"].get("losers", [{}])[0].get("t") if d["pulse"].get("losers") else None}, f)
    except Exception: pass

def collect():
    store = SQLiteStore()
    pulse = market.load_market_pulse() or {}
    macro = market.load_macro_pulse() or {}
    regime = market.compute_regime(macro) if macro else {}
    events, event_window_h, event_note = load_window(store, 24)
    for e in events:
        e["geo"] = any((t or "").split("-")[0] in GEO_TAGS for t in e.get("triggers", []))
    themes = theme_counts(events)
    movers_t = [m["t"] for m in (pulse.get("gainers", []) + pulse.get("losers", []))[:8]]
    st_sent, st_radar = fetch_stocktwits(movers_t)
    reddit = {}
    for ev in store.recent_all_events(hours=24):
        try: srcs = json.loads(ev.get("sources_json") or "[]")
        except Exception: srcs = []
        for s in srcs:
            n = s.get("name", "")
            if n.startswith("r/"): reddit[n] = reddit.get(n, 0) + 1
    sources_active = sorted({(e.get("source") or "").split(" +")[0] for e in events if e.get("source")})
    social_pulse = {}
    try:
        with open(os.path.join(market.DATA, "social_pulse.json")) as f: social_pulse = json.load(f)
    except Exception: pass
    headlines = sorted(events, key=lambda x: -(x.get("ts") or 0))[:8]
    sectors = {}
    for m in pulse.get("mega_caps", []):
        if m.get("pct") is not None:
            sectors.setdefault(m.get("s", "Other"), []).append(m["pct"])
    sector_tape = sorted(((k, sum(v) / len(v)) for k, v in sectors.items()), key=lambda x: -x[1])
    im_all = {x["sym"]: x for x in macro.get("instruments", [])}
    curve_pts = {}
    for s, n in (("TVC:US02Y", "2Y"), ("TVC:US05Y", "5Y"), ("TVC:US10Y", "10Y"), ("TVC:US30Y", "30Y")):
        i = im_all.get(s)
        if i and i.get("price") is not None: curve_pts[n] = i["price"]
    hist = []
    try:
        with open(YIELD_FILE) as f: hist = json.load(f)
    except Exception: pass
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if curve_pts:
        hist = [h for h in hist if h.get("day") != day]
        sp = None
        if "2Y" in curve_pts and "10Y" in curve_pts: sp = (curve_pts["10Y"] - curve_pts["2Y"]) * 100
        hist.append({"day": day, "ts": time.time(), "pts": curve_pts, "spread2s10s": sp})
        hist = hist[-60:]
        try:
            with open(YIELD_FILE, "w") as f: json.dump(hist, f)
        except Exception: pass
    return {"store": store, "pulse": pulse, "macro": macro, "regime": regime, "events": events,
            "geo_events": [e for e in events if e.get("geo")], "themes": themes,
            "st_radar": st_radar, "reddit": reddit, "sources_active": sources_active,
            "headlines": headlines, "sector_tape": sector_tape,
            "curve_pts": curve_pts, "yield_hist": hist, "social_pulse": social_pulse,
            "event_window_h": event_window_h, "event_note": event_note}

ANALYSIS_PROMPT = """You are the editor of a financial-and-geopolitical intelligence gazette.
Write TENTATIVE, quantitative, complete-sentence analysis. Rules:
- Use ONLY data present below; never invent tickers, numbers, events, or countries.
- NEVER use dollar signs or absolute price levels; express all moves in percent only.
- Balance geopolitical and economic analysis equally.
- Do not infer causality from coincident news and prices. Describe co-movement,
  not a verified catalyst. Do not call correlation a direct effect.
- Blogs and institutional feeds are NOT retail sentiment. Missing Reddit,
  StockTwits or X coverage means sentiment is unavailable, not neutral.
- Do not treat fallback confidence or stored claims as verified facts.
- No unsupported predictions or invented links between unrelated stories.
- Lead: at most 45 words. Other prose fields: at most 35 words.
- Headline: at most 12 words. Never end a field mid-sentence.
- NO EMOJIS. Complete sentences only. Each field under 600 chars.
Return ONLY this JSON:
{
  "headline": "serif-style front-page headline, max 90 chars",
  "lead": "3-sentence lead paragraph tying geopolitics AND markets together",
  "geopol_read": "2-3 sentences: geopolitical developments and their market transmission channels",
  "market_read": "2-3 sentences: equities, rates, FX, commodities behavior and divergences",
  "social_read": "1-2 sentences: retail/social chatter vs price action",
  "cross_asset": "2 sentences: observed cross-asset moves; clearly separate hypotheses from facts",
  "outlook": "1-2 sentences: catalysts and percent-level moves to watch next 24 hours",
  "key_risk": "1 sentence: single most important risk or opportunity",
  "delta": "1-2 sentences: what changed vs the previous edition"
}

PREVIOUS EDITION:
__PREV__

CURRENT DATA:
__DATA__"""

REQUIRED_KEYS = ("headline", "lead", "geopol_read", "market_read", "social_read",
                 "cross_asset", "outlook", "key_risk", "delta")

def _data_text(d):
    L = []
    for e in d["events"][:10]:
        L.append("EVENT [%s/%s] %s (src: %s)" % (e.get("severity"), e.get("status"), e.get("title"), e.get("source")))
    for m in (d["pulse"].get("gainers", []) + d["pulse"].get("losers", []))[:8]:
        L.append("MOVER %s %+.2f%%" % (m["t"], m["pct"]))
    for m in d["pulse"].get("hour_movers", [])[:5]:
        L.append("1H-MOVER %s %+.2f%% (1h)" % (m["t"], m["hour_chg"]))
    for i in d["macro"].get("instruments", []):
        if i.get("pct") is not None: L.append("MACRO %s %+.2f%%" % (i["name"], i["pct"]))
    for k, v in d["regime"].items(): L.append("REGIME %s = %s" % (k, v))
    for k, v in d["sector_tape"][:6]: L.append("SECTOR %s %+.2f%%" % (k, v))
    for k, v in sorted(d["themes"].items(), key=lambda x: -x[1])[:6]:
        L.append("THEME %s x%d" % (_clean(DOMAIN_NAMES.get(k, k)), v))
    if d["st_radar"]: L.append("STOCKTWITS " + " | ".join([_clean(r) for r in d["st_radar"][:6]]))
    if d["reddit"]:
        L.append("REDDIT " + ", ".join("%s x%d" % (k, v) for k, v in sorted(d["reddit"].items(), key=lambda x: -x[1])[:5]))
    sp = d.get("social_pulse", {})
    if sp.get("counts"):
        L.append("SOCIAL LANES " + ", ".join("%s=%d" % (k, v) for k, v in sorted(sp["counts"].items())[:8]))
    for t in sp.get("top", [])[:6]:
        L.append("CHATTER [%s] %s" % (t.get("src"), t.get("t")))
    if d["sources_active"]: L.append("SOURCES: " + ", ".join(d["sources_active"][:15]))
    return "\n".join(L)

def _prev_text(prev):
    if not prev: return "First edition of this cycle - no prior comparison."
    L = ["Previous edition %s UTC:" % datetime.fromtimestamp(prev.get("ts", 0), timezone.utc).strftime("%H:%M")]
    if prev.get("summary"): L.append("Prev lead: %s" % prev["summary"][:200])
    if prev.get("event_titles"): L.append("Prev events: %s" % ", ".join(prev["event_titles"][:5]))
    return "\n".join(L)

def _fallback_analysis(d, prev):
    ev, pulse, regime = d["events"], d["pulse"], d["regime"]
    g, l = pulse.get("gainers", []), pulse.get("losers", [])
    lead = ("led by %s +%.1f%%" % (g[0]["t"], g[0]["pct"])) if g else "quiet"
    lag = ("; %s %.1f%% lags" % (l[0]["t"], l[0]["pct"])) if l else ""
    mkt = "Equities %s%s. VIX %s; 2s10s %s." % (lead, lag, regime.get("vix", "n/a"), regime.get("curve_2s10s", "n/a"))
    geo = ("Geopolitical desk: %s." % (d["geo_events"][0].get("title") or "")) if d["geo_events"] else "Geopolitical desk: no major developments in window."
    news = ("Dominant cluster: %s." % _clean(DOMAIN_NAMES.get(sorted(d["themes"].items(), key=lambda x: -x[1])[0][0], "Mixed"))) if d["themes"] else "No dominant cluster."
    if ev: news += " Top event: %s." % (ev[0].get("title") or "")
    soc = " | ".join([_clean(r) for r in d["st_radar"][:4]]) if d["st_radar"] else "Retail sentiment coverage is insufficient for an assessment."
    if d["reddit"]: soc += " Reddit: " + ", ".join("%s x%d" % (k, v) for k, v in sorted(d["reddit"].items(), key=lambda x: -x[1])[:3])
    headline = (ev[0].get("title") or "Quiet session across markets") if ev else "Quiet session across markets"
    return {"headline": headline, "lead": (geo + " " + mkt)[:600], "geopol_read": geo[:600],
            "market_read": mkt[:600], "social_read": soc[:600], "cross_asset": mkt[:600],
            "outlook": "Watch for continuation in dominant themes; monitor pre-market futures for gap risk.",
            "key_risk": ("Monitor for escalation in the dominant cluster." if ev else "Quiet tape - gap-on-open risk."),
            "delta": ("First edition - no prior comparison." if not prev else "Prior edition %s UTC." % datetime.fromtimestamp(prev.get("ts", 0), timezone.utc).strftime("%H:%M"))}

def analyze(d):
    prev = _load_prev()
    d["previous_edition"] = prev
    out = None
    try:
        prompt = ANALYSIS_PROMPT.replace("__DATA__", _data_text(d)).replace("__PREV__", _prev_text(prev))
        content = chat([
            {"role": "system", "content": "Gazette editor. Output ONLY valid JSON. NO EMOJIS. NO DOLLAR FIGURES."},
            {"role": "user", "content": prompt}
        ])
        m = re.search(r"\{[\s\S]*\}", content)
        if m:
            obj = json.loads(m.group(0))
            if all(isinstance(obj.get(k), str) and len(obj.get(k)) >= 10 for k in REQUIRED_KEYS):
                out = obj
    except Exception: pass
    if out is None:
        out, llm = _fallback_analysis(d, prev), False
    else:
        llm = True
    for k in REQUIRED_KEYS:
        out[k] = _scrub(out[k]) or out[k]
    return out, llm, prev

# Layout is isolated from collection and API calls for offline visual testing.
from gazette_render import render_p1 as _page1, render_p2 as _page2

def render_p1(d, a, llm_ok):
    _page1(d, a, llm_ok, P1)

def render_p2(d, a, llm_ok):
    _page2(d, a, llm_ok, P2)

def _discord_webhook_url(wait=False):
    raw=(os.environ.get("DISCORD_WEBHOOK") or "").strip()
    p=urlsplit(raw)
    if p.scheme!="https" or p.hostname not in ("discord.com","discordapp.com") or not re.fullmatch(r"/api(?:/v\d+)?/webhooks/\d+/[A-Za-z0-9_-]+",p.path):
        raise RuntimeError("DISCORD_WEBHOOK is missing or invalid")
    return urlunsplit((p.scheme,p.netloc,p.path,"wait=true" if wait else "",""))

def discord_webhook_info():
    r=requests.get(_discord_webhook_url(False),timeout=(10,20))
    if r.status_code!=200:
        raise RuntimeError("Discord webhook probe HTTP %d" % r.status_code)
    try: info=r.json()
    except ValueError: raise RuntimeError("Discord webhook probe returned invalid JSON") from None
    channel=str(info.get("channel_id") or "unknown")
    expected=(os.environ.get("DISCORD_EXPECTED_CHANNEL_ID") or "").strip()
    if expected and channel!=expected:
        raise RuntimeError("Discord webhook points to channel %s, expected %s" % (channel,expected))
    print("Gazette Discord route confirmed: channel_id=%s webhook_id=%s name=%s" % (
        channel,str(info.get("id") or "unknown"),str(info.get("name") or "unnamed").replace("\n"," ")[:80]))
    return info

def send(pages):
    if not pages or any(not os.path.isfile(p) for p in pages):
        raise RuntimeError("Gazette pages are missing")
    discord_webhook_info()
    url=_discord_webhook_url(True)
    for attempt in range(2):
        with ExitStack() as stack:
            files=[("files[%d]" % i,(os.path.basename(p),stack.enter_context(open(p,"rb")),"image/png")) for i,p in enumerate(pages)]
            r=requests.post(url,files=files,data={"payload_json":json.dumps({
                "content":"🗞️ **THE AGGREGATE GAZETTE** (tentative, machine-compiled)",
                "allowed_mentions":{"parse":[]}})},timeout=(10,60))
        if r.status_code==429 and attempt==0:
            try: delay=min(max(float(r.json().get("retry_after",2)),1),30)
            except (ValueError,TypeError): delay=2
            time.sleep(delay)
            continue
        if r.status_code!=200:
            raise RuntimeError("Discord HTTP %d: %s" % (r.status_code,r.text[:120]))
        try:
            body=r.json(); message_id=str(body["id"]); channel_id=str(body.get("channel_id") or "unknown")
        except (ValueError,KeyError,TypeError):
            raise RuntimeError("Discord did not return a verifiable message receipt") from None
        expected=(os.environ.get("DISCORD_EXPECTED_CHANNEL_ID") or "").strip()
        if expected and channel_id!=expected:
            raise RuntimeError("Discord receipt channel mismatch: %s != %s" % (channel_id,expected))
        print("Gazette delivery confirmed: message_id=%s channel_id=%s pages=%d" % (message_id,channel_id,len(pages)))
        return message_id
    raise RuntimeError("Discord rate limit persisted after retry")

if __name__ == "__main__":
    os.makedirs(REPORTS, exist_ok=True)
    data = collect()
    analysis, llm_ok, prev = analyze(data)
    render_p1(data, analysis, llm_ok)
    render_p2(data, analysis, llm_ok)
    send([P1, P2])
    # Only a confirmed Discord edition becomes the comparison baseline.
    _save_prev(analysis, data)
