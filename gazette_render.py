"""Original Gazette layout; offline rendering with honest metrics."""
import math, re, textwrap, time
from datetime import datetime, timezone
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from briefing import DOMAIN_NAMES

PAPER, INK, MUT2, CARDL = "#F6F1E7", "#1C1B18", "#514B43", "#C8BDAA"
GEO, MKT, SOC, UP, DN, HI = "#7D2A2A", "#1F3864", "#705514", "#285C38", "#9D3029", "#896000"
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

def _fmt_price(p, t):
    if not finite(p): return "-"
    if t in ("forex",): return "%.4f" % p
    if t in ("bond",): return "%.2f%%" % p
    if p >= 10000: return "%.0f" % p
    if p >= 100: return "%.1f" % p
    return "%.2f" % p


def finite(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)

def number(value, fmt):
    return fmt % value if finite(value) else "-"

def pct(value):
    return number(value, "%+.2f%%")

def freshness(ts):
    if not finite(ts) or ts <= 0: return "missing"
    if ts > 100_000_000_000: ts /= 1000
    minutes = (time.time() - ts) / 60
    if minutes < -5: return "future timestamp"
    minutes = max(0, minutes)
    if minutes < 120: return "%dm old" % minutes
    return ("STALE %.1fh" if minutes > 1200 else "%.1fh old") % (minutes/60)

def market_cap(value):
    if not finite(value) or value <= 0: return "cap n/a"
    if value >= 1e12: return "$%.2fT" % (value/1e12)
    if value >= 1e9: return "$%.1fB" % (value/1e9)
    return "$%.0fM" % (value/1e6)

def measured_lines(A, value, width, size, weight="normal", family="DejaVu Sans"):
    renderer = A.figure.canvas.get_renderer()
    prop = FontProperties(family=family, size=size, weight=weight)
    limit = width*A.bbox.width
    lines, line = [], ""
    for word in _clean(str(value or "")).split():
        candidate = (line+" "+word).strip()
        if renderer.get_text_width_height_descent(candidate, prop, False)[0] > limit and line:
            lines.append(line); line = ""
        while renderer.get_text_width_height_descent(word, prop, False)[0] > limit:
            n = len(word)-1
            while n > 1 and renderer.get_text_width_height_descent(word[:n], prop, False)[0] > limit:
                n -= 1
            if line: lines.append(line); line = ""
            lines.append(word[:n]); word = word[n:]
        line = (line+" "+word).strip()
    if line: lines.append(line)
    return lines

def one_line(A, value, width, size, weight="normal"):
    lines = measured_lines(A, value, width, size, weight)
    if not lines: return ""
    if len(lines) == 1: return lines[0]
    line = lines[0]
    while line and len(measured_lines(A, line+"...", width, size, weight)) > 1:
        line = line[:-1]
    return line.rstrip()+"..."

def prepare(data):
    d = dict(data)
    for key in ("pulse", "macro", "regime", "themes", "social_pulse", "reddit", "curve_pts"):
        d[key] = dict(d.get(key) or {})
    for key in ("events", "geo_events", "headlines", "sources_active", "st_radar", "sector_tape", "yield_hist"):
        d[key] = list(d.get(key) or [])
    d.setdefault("store", None)
    d.setdefault("event_window_h", 24)
    # Explicitly invalid snapshots must not appear as valid zeros.
    for key in ("pulse", "macro"):
        if d[key].get("valid") is False:
            d[key] = {"updated": d[key].get("updated"), "valid": False}
    if d["macro"].get("valid") is False:
        d["regime"], d["curve_pts"] = {}, {}
    if d["pulse"].get("valid") is False: d["sector_tape"] = []
    for key in ("mega_caps", "gainers", "losers", "hour_movers"):
        field = "hour_chg" if key == "hour_movers" else "pct"
        d["pulse"][key] = [m for m in d["pulse"].get(key, []) if finite(m.get(field))]
    d["macro"]["instruments"] = [
        {**i, "pct": i.get("pct") if finite(i.get("pct")) else None,
         "price": i.get("price") if finite(i.get("price")) else None}
        for i in d["macro"].get("instruments", [])]
    return d

def quality(d):
    rows = d.get("events", [])[:8]
    ids = {e.get("event_id") for e in rows if e.get("event_id")}
    store = d.get("store")
    try: claims = str(sum(store.get_claim_count(i) for i in ids)) if store else "unavailable"
    except Exception: claims = "unavailable"
    return "Stored claims (not verified): %s | first %d displayed events | named sources: %d" % (
        claims, len(rows), len(set(d.get("sources_active", []))))

def ticker_mentions(events):
    counts = {}
    for e in events:
        for t in set(e.get("tickers") or []):
            if isinstance(t, str): counts[t] = counts.get(t, 0)+1
    return ", ".join("%s %d" % item for item in sorted(counts.items(), key=lambda item: -item[1])[:5]) or "unavailable"

def edition_change(d):
    previous = d.get("previous_edition")
    if not previous: return "Previous-edition comparison unavailable."
    old = {_clean(t).lower() for t in previous.get("event_titles", [])}
    titles = {_clean(e.get("title")).lower() for e in d.get("events", [])[:8]}
    return "%d of %d leading titles absent from previous top-eight list; not necessarily new events." % (len(titles-old), len(titles))


# ================= LAYOUT PRIMITIVES =================
def _chars(w, size): return int(w * 2300 / size)

def _panel(A, x, ytop, w, h, title=None, color=INK):
    A.add_patch(plt.Rectangle((x, ytop - h), w, h, fill=False, color=CARDL, lw=1.0))
    yy = ytop - 0.012
    if title:
        A.text(x + 0.008, ytop - 0.021, _clean(title), color=color, fontsize=11.5, weight="bold")
        A.add_patch(plt.Rectangle((x + 0.008, ytop - 0.030), w - 0.016, 0.0015, color=color))
        yy = ytop - 0.046
    return x + 0.008, yy, w - 0.016

def _block(A, x, y, w, text, size=10, color=INK, lh=0.019, maxl=6):
    for line in measured_lines(A, text, w, size)[:maxl]:
        A.text(x, y, line, color=color, fontsize=size); y -= lh
    return y

def _lax(ax):
    ax.set_facecolor(PAPER)
    ax.tick_params(colors=MUT2, labelsize=9.5, pad=4)
    for label in list(ax.get_xticklabels()) + list(ax.get_yticklabels()):
        label.set_fontweight("bold")
    for s in ax.spines.values(): s.set_color(CARDL)
    ax.title.set_color(INK); ax.title.set_fontsize(10.5); ax.title.set_weight("bold")
    ax.xaxis.label.set_fontweight("bold"); ax.yaxis.label.set_fontweight("bold")

def _masthead(A, title, r1, r2):
    A.text(.03, .978, r1, color=MUT2, fontsize=10)
    A.text(.97, .978, r2, color=MUT2, fontsize=10, ha="right")

# ================= PAGE 1 =================
def render_p1(d, a, llm_ok, path):
    d = prepare(d)
    fig = plt.figure(figsize=(19.2, 10.8), dpi=200); fig.patch.set_facecolor(PAPER)
    A = fig.add_axes([0, 0, 1, 1]); A.set_axis_off(); A.set_xlim(0, 1); A.set_ylim(0, 1)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    if d.get("sample"): now = "SYNTHETIC SAMPLE - NOT LIVE DATA | " + now
    session = ("US SESSION SNAPSHOT" if d["pulse"].get("session_open") else "PREVIOUS SESSION SNAPSHOT")
    vol = (datetime.now(timezone.utc) - datetime(2026, 1, 1, tzinfo=timezone.utc)).days
    _masthead(A, "THE AGGREGATE GAZETTE", "Vol. %d · Market & Geopolitical Intelligence" % vol, "%s · %s" % (now, session))

    pulse, macro, regime, store = d["pulse"], d["macro"], d["regime"], d["store"]
    rolls = {"bullish": 0, "neutral": 0, "bearish": 0}
    for e in d["events"]:
        s = (e.get("sentiment") or "").lower()
        if s in rolls: rolls[s] += 1
    tot = max(sum(rolls.values()), 1)
    mega = [m for m in pulse.get("mega_caps", []) if m.get("pct") is not None]
    adv = sum(1 for m in mega if m["pct"] > 0)
    hi_crit = sum(1 for e in d["events"] if (e.get("severity") or "") in ("High", "Critical"))
    im = {i["name"]: i for i in macro.get("instruments", [])}
    stats = [("EVENTS %dH" % d["event_window_h"], str(len(d["events"])), "tracked"), ("HIGH/CRIT", str(hi_crit), "severity"),
             ("BULLISH", "%d%%" % round(100 * rolls["bullish"] / tot) if sum(rolls.values()) else "-", "classified news"),
             ("BREADTH", "%d/%d" % (adv, len(mega)) if mega else "-", "mega-cap sample"),
             ("VIX", number(im.get("VIX", {}).get("price"), "%.1f"), regime.get("vix", "")),
             ("2s10s", regime.get("curve_2s10s", "-"), "curve"),
             ("DXY", pct(im.get("US Dollar Index", {}).get("pct")), regime.get("dxy", "")),
             ("WTI", pct(im.get("WTI Crude", {}).get("pct")), "crude")]
    x = 0.03; w = 0.94 / 8
    for i, (lab, val, sub) in enumerate(stats):
        cx = x + i * w
        if i: A.add_patch(plt.Rectangle((cx, 0.883), 0.0012, 0.048, color=INK))
        A.text(cx + w / 2, 0.925, _clean(lab), color=MUT2, fontsize=9, ha="center", weight="bold")
        A.text(cx + w / 2, 0.902, _clean(val), color=INK, fontsize=15, ha="center", weight="bold")
        A.text(cx + w / 2, 0.886, _clean(sub), color=MUT2, fontsize=9, ha="center")
    A.add_patch(plt.Rectangle((0.03, 0.878), 0.94, 0.0015, color=INK))

    headline = measured_lines(A, a["headline"], .35, 16, "bold", "serif")[:2]
    for row, line in enumerate(headline):
        A.text(.335, .849-row*.025, line, color=INK, fontsize=16, weight="bold", fontfamily="serif")
    A.add_patch(plt.Rectangle((.335, .805), .35, .0015, color=HI))
    body = measured_lines(A, a["lead"], .33, 10.5)[:4]
    y = .781
    if body and body[0]:
        A.text(0.335, y - 0.006, body[0][0], color=INK, fontsize=24, weight="bold", fontfamily="serif")
        A.text(0.350, y, body[0][1:], color=INK, fontsize=11)
        y -= 0.022
        for line in body[1:]:
            A.text(0.335, y, line, color=INK, fontsize=11); y -= 0.020
    hy = .681
    cells = mega[:12]; cw = 0.35 / max(len(cells), 1)
    for i, m in enumerate(cells):
        col = UP if m["pct"] > 0 else DN
        A.add_patch(plt.Rectangle((0.335 + i * cw, hy - 0.036), cw * 0.92, 0.033, color=col,
                                  alpha=1.0))
        A.text(0.335 + i * cw + cw / 2, hy - 0.013, m["t"], color="#fff", fontsize=8, ha="center", weight="bold")
        A.text(0.335 + i * cw + cw / 2, hy - 0.027, "%+.1f%%" % m["pct"], color="#fff", fontsize=7.5, ha="center")

    px, py, pw = _panel(A, 0.335, 0.630, 0.35, 0.295, "EVENT LEDGER - TOP CLUSTERS", HI)
    y = py
    for e in d["events"][:7]:
        sev = e.get("severity") or "Low"
        A.add_patch(plt.Rectangle((px, y - 0.004), 0.005, 0.014, color=SEV_COLOR.get(sev, MUT2)))
        A.text(px + 0.010, y, one_line(A, e.get("title"), pw-.012, 9.5, "bold"), color=INK, fontsize=10, weight="bold")
        conf = e.get("confidence")
        A.text(px + 0.010, y - 0.015, "%s | score %s/100 | %s" % (sev, conf if conf is not None else "-", freshness(e.get("ts"))), color=MUT2, fontsize=9)
        y -= 0.034

    px, py, pw = _panel(A, 0.03, 0.845, 0.27, 0.51, "WORLD & GEOPOLITICS", GEO)
    y = _block(A, px, py, pw, a["geopol_read"], 10, INK, 0.020, 4)
    y -= 0.006
    A.text(px, y, "GEOPOLITICAL WATCHLIST", color=GEO, fontsize=10, weight="bold"); y -= 0.019
    for e in d["geo_events"][:4]:
        sev = e.get("severity") or "Low"
        A.add_patch(plt.Rectangle((px, y - 0.003), 0.005, 0.014, color=SEV_COLOR.get(sev, MUT2)))
        A.text(px + 0.010, y, one_line(A, e.get("title"), pw-.012, 9.5, "bold"), color=INK, fontsize=10, weight="bold")
        conf = e.get("confidence")
        A.text(px + 0.010, y - 0.014, "%s | %s | %s" % (sev, (str(conf) + "/100") if conf is not None else "-", (e.get("source") or "")[:22]), color=MUT2, fontsize=9)
        y -= 0.033
    y -= 0.004
    A.text(px, y, "HIGH / CRITICAL EVENT SHARE", color=GEO, fontsize=10, weight="bold"); y -= 0.018
    score = 100 * hi_crit / max(len(d["events"]), 1)
    A.add_patch(plt.Rectangle((px, y - 0.006), pw * .86, 0.011, color=CARDL))
    A.add_patch(plt.Rectangle((px, y - 0.006), pw * .86 * score / 100.0, 0.011, color=GEO))
    A.text(px + pw, y - 0.006, "%d%%" % score if d["events"] else "-", color=GEO, fontsize=10, weight="bold", ha="right")
    y -= 0.026
    A.text(px, y, "ACTIVE NEWS SOURCES", color=GEO, fontsize=10, weight="bold"); y -= 0.016
    for line in _wrap(", ".join(d.get("sources_active", [])[:14]) or "No sources in window.", _chars(pw, 9))[:5]:
        A.text(px, y, line, color=MUT2, fontsize=9); y -= 0.016
    y -= 0.004
    A.text(px, y, "SOCIAL CHATTER", color=SOC, fontsize=10, weight="bold"); y -= 0.016
    sp = d.get("social_pulse", {})
    for t in sp.get("top", [])[:3]:
        A.text(px, y, one_line(A, "[%s] %s" % (t.get("src", ""), t.get("t", "")), pw, 8.5), color=INK, fontsize=9); y -= 0.015

    px, py, pw = _panel(A, 0.70, 0.845, 0.27, 0.51, "MARKETS & ECONOMY", MKT)
    y = _block(A, px, py, pw, a["market_read"], 10, INK, 0.020, 4)
    y -= 0.006
    A.text(px, y, "SECTOR SAMPLE (avg %chg)", color=MKT, fontsize=10, weight="bold"); y -= 0.017
    for k, v in d["sector_tape"][:6]:
        A.text(px, y, _clean(k)[:18], color=MUT2, fontsize=9)
        A.add_patch(plt.Rectangle((px + pw * 0.42, y + 0.002), min(abs(v) / 2.0, 1.0) * pw * 0.42, 0.009, color=UP if v > 0 else DN))
        A.text(px + pw, y, "%+.2f%%" % v, color=UP if v > 0 else DN, fontsize=9, ha="right", weight="bold")
        y -= 0.016
    y -= 0.004
    A.text(px, y, "TOP MOVERS", color=MKT, fontsize=10, weight="bold"); y -= 0.016
    for m in (pulse.get("gainers", [])[:2] + pulse.get("losers", [])[:2]):
        A.text(px, y, m["t"], color=INK, fontsize=10, weight="bold")
        A.text(px + pw, y, "%+.2f%%" % m["pct"], color=UP if m["pct"] > 0 else DN, fontsize=10, ha="right", weight="bold")
        y -= 0.016
    y -= 0.004
    A.text(px, y, "MACRO SNAPSHOT", color=MKT, fontsize=10, weight="bold"); y -= 0.016
    for nm in ("S&P 500", "VIX", "US 10Y Yield", "WTI Crude", "Gold", "US Dollar Index"):
        i = im.get(nm, {})
        p = i.get("pct")
        A.text(px, y, nm, color=MUT2, fontsize=9)
        A.text(px + pw, y, "%+.2f%%" % p if p is not None else "-", color=UP if (p or 0) > 0 else (DN if (p or 0) < 0 else MUT2), fontsize=9, ha="right", weight="bold")
        y -= 0.016
    y -= 0.004
    A.text(px, y, "RATES & FX MOVERS", color=MKT, fontsize=10, weight="bold"); y -= 0.016
    rfx = sorted([i for i in macro.get("instruments", []) if i.get("type") in ("forex", "bond") and i.get("pct") is not None], key=lambda i: -abs(i["pct"]))[:4]
    for i in rfx:
        A.text(px, y, _clean(i["name"])[:16], color=MUT2, fontsize=9)
        A.text(px + pw, y, "%+.2f%%" % i["pct"], color=UP if i["pct"] > 0 else DN, fontsize=9, ha="right", weight="bold")
        y -= 0.016

    for (bx, bw, btitle, bcol) in ((0.03, 0.29, "WHAT CHANGED", HI), (0.36, 0.29, "SOCIAL PULSE", SOC), (0.70, 0.27, "OUTLOOK & KEY RISK", DN)):
        px, py, pw = _panel(A, bx, 0.300, bw, 0.245, btitle, bcol)
        y = py
        if btitle == "WHAT CHANGED":
            y = _block(A, px, y, pw, a["delta"], 10, INK, 0.019, 4)
            y -= .012
            y = _block(A, px, y, pw, edition_change(d), 9, MUT2, .018, 3)
            _block(A, px, y-.01, pw, "%dh window | %d displayed events | %d named sources" % (d["event_window_h"], len(d["events"]), len(d["sources_active"])), 9, MUT2, .018, 2)
        elif btitle == "SOCIAL PULSE":
            y = _block(A, px, y, pw, a["social_read"], 10, INK, 0.019, 3)
            for line in ([_clean(r)[:46] for r in d["st_radar"][:2]] or ["No qualifying StockTwits signal."]):
                A.text(px, y, line, color=MUT2, fontsize=9); y -= 0.016
            cnt = sp.get("coverage") or sp.get("counts", {})
            if cnt:
                A.text(px, y, "LANES: " + " · ".join("%s %d" % (k, v) for k, v in sorted(cnt.items())[:5]), color=MUT2, fontsize=9); y -= 0.016
            _block(A, px, .09, pw, "News ticker mentions: " + ticker_mentions(d["events"]), 9, MUT2, .018, 2)
            for t in sp.get("top", [])[:2]:
                A.text(px, y, one_line(A, "[%s] %s" % (t.get("src", ""), t.get("t", "")), pw, 8.5), color=INK, fontsize=9); y -= 0.015
        else:
            y = _block(A, px, y, pw, a["outlook"], 10, INK, 0.019, 3)
            _block(A, px, y-.014, pw, "Current: VIX %s | curve %s | WTI %s" % (regime.get("vix", "unavailable"), regime.get("curve_2s10s", "-"), pct(im.get("WTI Crude", {}).get("pct"))), 9, MUT2, .018, 3)
            yb = 0.300 - 0.245 + 0.010
            A.add_patch(plt.Rectangle((px, yb), pw, 0.042, color="#EAD9D2"))
            rk = _fit(a["key_risk"], _chars(pw, 9.5), 2)
            A.text(px + 0.006, yb + 0.028, rk[0] if rk else "", color=DN, fontsize=10, weight="bold")
            A.text(px + 0.006, yb + 0.012, rk[1] if len(rk) > 1 else "", color=DN, fontsize=10)

    A.text(.03, .038, quality(d), color=MUT2, fontsize=9)
    A.text(0.03, 0.020, "Narrative: %s | Charts from snapshots | Tentative - machine-compiled, not investment advice" % ("AI-generated; not independently verified" if llm_ok else "deterministic fallback"), color=MUT2, fontsize=9)
    A.text(0.97, 0.020, "Page 1 of 2", color=MUT2, fontsize=9, ha="right")
    fig.savefig(path, facecolor=PAPER); plt.close(fig)

# ================= PAGE 2 =================
def render_p2(d, a, llm_ok, path):
    d = prepare(d)
    fig = plt.figure(figsize=(19.2, 10.8), dpi=200); fig.patch.set_facecolor(PAPER)
    A = fig.add_axes([0, 0, 1, 1]); A.set_axis_off(); A.set_xlim(0, 1); A.set_ylim(0, 1)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    if d.get("sample"): now = "SYNTHETIC SAMPLE - NOT LIVE DATA | " + now
    _masthead(A, "MARKETS & DATA", "The Aggregate Gazette · Section B", now)
    pulse, macro, regime = d["pulse"], d["macro"], d["regime"]
    rolls = {"bullish": 0, "neutral": 0, "bearish": 0}
    for e in d["events"]:
        s = (e.get("sentiment") or "").lower()
        if s in rolls: rolls[s] += 1
    tot = max(sum(rolls.values()), 1)
    im = {i["name"]: i for i in macro.get("instruments", [])}
    status_line = "DATA STATUS  events %d/%dh · market %s · macro %s · social %s" % (
        len(d.get("events", [])), d.get("event_window_h", 24), freshness(pulse.get("updated")),
        freshness(macro.get("updated")), freshness(d.get("social_pulse", {}).get("ts")))
    A.text(0.5, 0.955, status_line, color=MUT2, fontsize=9, ha="center")

    A.text(.5, .937, quality(d), color=MUT2, fontsize=9, ha="center")
    ax = fig.add_axes([0.06, 0.755, 0.26, 0.145]); _lax(ax); ax.set_title("MEGA-CAP LEADERS (%CHG)", pad=6)
    mega = [m for m in pulse.get("mega_caps", []) if m.get("pct") is not None][:12]
    if mega:
        names = [m["t"] for m in mega][::-1]; vals = [m["pct"] for m in mega][::-1]
        ax.barh(names, vals, color=[UP if v > 0 else DN for v in vals], height=0.72)
        ax.axvline(0, color=MUT2, lw=0.6)
        mm = max([abs(v) for v in vals] + [0.1]); ax.set_xlim(-mm * 1.3, mm * 1.3)
    ax = fig.add_axes([0.06, 0.535, 0.26, 0.145]); _lax(ax); ax.set_title("SECTOR SAMPLE (avg %chg)", pad=6)
    if d["sector_tape"]:
        ks = [k[:14] for k, _ in d["sector_tape"][:8]][::-1]; vs = [v for _, v in d["sector_tape"][:8]][::-1]
        ax.barh(ks, vs, color=[UP if v > 0 else DN for v in vs], height=0.7)
        ax.axvline(0, color=MUT2, lw=0.6)
    ax = fig.add_axes([0.05, 0.335, 0.27, 0.13]); _lax(ax); ax.set_title("MOVERS: %CHG vs REL-VOLUME", pad=6)
    sig = [{"t": k, **v} for k, v in pulse.get("sig", {}).items() if v.get("pct") is not None and v.get("relvol")][:50]
    if sig:
        ax.scatter([v["pct"] for v in sig], [v["relvol"] for v in sig], c=[UP if v["pct"] > 0 else DN for v in sig], s=12, alpha=0.7)
        for v in sorted(sig, key=lambda x: -x["relvol"])[:4]:
            ax.annotate(_clean(v["t"]), (v["pct"], v["relvol"]), color=INK, fontsize=8.5, weight="bold", xytext=(4, 5), textcoords="offset points")
    ax.set_xlabel("Session change (%)", color=MUT2, fontsize=9.5, weight="bold", labelpad=3)

    px, py, pw = _panel(A, 0.34, 0.91, 0.36, 0.29, "MACRO & RATES - FULL BOARD", MKT)
    groups = {}
    for i in macro.get("instruments", []): groups.setdefault(i.get("type", "other"), []).append(i)
    yL, yR = py, py
    for gname, key, n in [("CASH INDICES", "index", 5), ("INDEX FUTURES", "index_future", 3), ("COMMODITIES", "commodity", 4)]:
        A.text(px, yL, gname, color=MUT2, fontsize=10, weight="bold"); yL -= 0.016
        rows = groups.get(key, [])[:n]
        if not rows:
            A.text(px, yL, "No data available", color=MUT2, fontsize=9); yL -= 0.016
        for i in rows:
            p = i.get("pct")
            A.text(px, yL, _clean(i["name"])[:16], color=INK, fontsize=10)
            A.text(px + pw * 0.30, yL, _fmt_price(i.get("price"), i.get("type")), color=MUT2, fontsize=9, ha="right")
            A.text(px + pw * 0.46, yL, "%+.2f%%" % p if p is not None else "-", color=UP if (p or 0) > 0 else (DN if (p or 0) < 0 else MUT2), fontsize=10, ha="right", weight="bold")
            yL -= 0.016
        yL -= 0.005
    for gname, key, n in [("FOREX", "forex", 5), ("YIELDS (% RELATIVE CHANGE)", "bond", 4)]:
        A.text(px + pw * 0.52, yR, gname, color=MUT2, fontsize=10, weight="bold"); yR -= 0.016
        rows = groups.get(key, [])[:n]
        if not rows:
            A.text(px + pw * 0.52, yR, "No data available", color=MUT2, fontsize=9); yR -= 0.016
        for i in rows:
            p = i.get("pct")
            A.text(px + pw * 0.52, yR, _clean(i["name"])[:14], color=INK, fontsize=10)
            A.text(px + pw, yR, "%+.2f%%" % p if p is not None else "-", color=UP if (p or 0) > 0 else (DN if (p or 0) < 0 else MUT2), fontsize=10, ha="right", weight="bold")
            yR -= 0.016
        yR -= 0.005
    A.text(px + pw * 0.52, yR, "REGIME", color=MUT2, fontsize=10, weight="bold"); yR -= 0.016
    for line in list(filter(None, [
        "VIX: %s" % regime.get("vix") if regime.get("vix") else None,
        "2s10s: %s%s" % (regime.get("curve_2s10s", ""), " INVERTED" if regime.get("curve_inverted") else "") if regime.get("curve_2s10s") else None,
        "DXY: %s" % regime.get("dxy") if regime.get("dxy") else None,
        "Oil: %s" % regime.get("oil_spike") if regime.get("oil_spike") else None])):
        A.text(px + pw * 0.52, yR, _clean(line), color=GEO, fontsize=10); yR -= 0.016

    ax = fig.add_axes([0.36, 0.34, 0.30, 0.24]); _lax(ax)
    hist = [h for h in d["yield_hist"] if h.get("spread2s10s") is not None]
    if len(hist) >= 3:
        ax.plot(range(len(hist)), [h["spread2s10s"] for h in hist], marker="o", color=GEO, lw=2.5, markersize=6)
        ax.axhline(0, color=MUT2, lw=0.6, ls="--")
        ax.set_title("2s10s SPREAD (bp) - TRAILING %d DAYS" % len(hist), pad=6)
        ax.set_xlabel("%s → %s" % (hist[0]["day"], hist[-1]["day"]), color=MUT2, fontsize=9.5, weight="bold", labelpad=3)
    else:
        pts = [(n, d["curve_pts"].get(n)) for n in ("2Y", "5Y", "10Y", "30Y") if d["curve_pts"].get(n) is not None]
        if pts:
            ax.plot([n for n, _ in pts], [p for _, p in pts], marker="o", color=GEO, lw=2.5, markersize=8)
            for n, p in pts: ax.annotate("%.2f%%" % p, (n, p), textcoords="offset points", xytext=(0, 12), color=INK, fontsize=10, weight="bold", ha="center")
            ax.margins(y=.25)
            ax.set_title("US YIELD CURVE (%) - CURRENT SNAPSHOT", pad=10)
        else:
            ax.text(0.5, 0.5, "no data", color=MUT2, ha="center")

    ax = fig.add_axes([0.72, 0.80, 0.25, 0.11]); _lax(ax); ax.set_title("COMMODITIES (SESSION CHANGE %)", pad=6)
    coms = [i for i in groups.get("commodity", []) if i.get("pct") is not None]
    if not coms:
        ax.text(0.5, 0.5, "No data", color=MUT2, ha="center", transform=ax.transAxes)
    else:
        ax.bar([_clean(i["name"])[:8] for i in coms], [i["pct"] for i in coms], color=[UP if i["pct"] > 0 else DN for i in coms])
        ax.axhline(0, color=MUT2, lw=0.6)

    A.text(0.71, 0.77, "RISERS & FALLERS (SINCE LAST UPDATE)", color=HI, fontsize=11, weight="bold")
    A.add_patch(plt.Rectangle((0.71, 0.762), 0.26, 0.0015, color=HI))
    deltas = pulse.get("deltas", {})
    if deltas:
        up = sum(1 for v in deltas.values() if v > 0.05)
        dn = sum(1 for v in deltas.values() if v < -0.05)
        fl = len(deltas) - up - dn
        axp = fig.add_axes([0.72, 0.56, 0.115, 0.19]); axp.set_facecolor(PAPER); axp.set_axis_off()
        axp.pie([up, dn, fl], colors=[UP, DN, "#B9B0A0"], startangle=90, wedgeprops={"linewidth": 0.8, "edgecolor": PAPER})
        A.text(0.85, 0.70, "Rising %d" % up, color=UP, fontsize=10.5, weight="bold")
        A.text(0.85, 0.66, "Falling %d" % dn, color=DN, fontsize=10.5, weight="bold")
        A.text(0.85, 0.62, "Unchanged %d" % fl, color=MUT2, fontsize=10.5, weight="bold")
    else:
        A.text(0.72, 0.66, "No previous snapshot yet -", color=MUT2, fontsize=10)
        A.text(0.72, 0.63, "baseline building.", color=MUT2, fontsize=10)

    A.text(0.71, 0.52, "1-HOUR MOVERS (LARGE CAPS)", color=HI, fontsize=11, weight="bold")
    A.add_patch(plt.Rectangle((0.71, 0.512), 0.26, 0.0015, color=HI))
    y = 0.49
    hm = pulse.get("hour_movers", [])
    if not hm:
        A.text(0.71, y, "No qualifying 1h observations; coverage may be incomplete.", color=MUT2, fontsize=10); y -= 0.020
    for m in hm[:5]:
        A.text(0.71, y, m["t"], color=INK, fontsize=10, weight="bold")
        A.text(0.80, y, "%+.2f%% (1h)" % m["hour_chg"], color=UP if m["hour_chg"] > 0 else DN, fontsize=10, weight="bold")
        A.text(0.97, y, "session %s | %s" % (pct(m.get("pct")), market_cap(m.get("mcap"))), color=MUT2, fontsize=9, ha="right")
        y -= 0.020
    y -= 0.006
    A.text(0.71, y, "FX & RATES MOVERS", color=MKT, fontsize=10, weight="bold"); y -= 0.017
    for i in sorted([i for i in macro.get("instruments", []) if i.get("type") in ("forex", "bond") and i.get("pct") is not None], key=lambda i: -abs(i["pct"]))[:4]:
        A.text(0.71, y, _clean(i["name"])[:16], color=MUT2, fontsize=9)
        A.text(0.97, y, "%+.2f%%" % i["pct"], color=UP if i["pct"] > 0 else DN, fontsize=9, ha="right", weight="bold")
        y -= 0.016

    A.add_patch(plt.Rectangle((0.03, 0.305), 0.94, 0.0015, color=INK))
    A.text(0.03, 0.288, "NEWS UPDATES - PAST %d HOURS (UTC)" % d["event_window_h"], color=GEO, fontsize=12, weight="bold")
    A.add_patch(plt.Rectangle((0.03, 0.280), 0.94, 0.0015, color=GEO))
    for i, e in enumerate(d["headlines"][:8]):
        colx = 0.03 + (i % 2) * 0.485
        yy = 0.263 - (i // 2) * 0.017
        ts = datetime.fromtimestamp(e.get("ts") or 0, timezone.utc).strftime("%H:%M")
        t = _clean(e.get("title"))
        t = one_line(A, t, .42, 9)
        A.text(colx, yy, "[%s] %s" % (ts, t), color=INK, fontsize=9)
    if not d["headlines"]:
        note = _clean(d.get("event_note") or "No fresh event headlines in the selected window.")
        A.text(0.03, 0.260, note[:150], color=MUT2, fontsize=10)

    sp2 = d.get("social_pulse", {})
    tops = sp2.get("top", [])[:4]
    A.text(0.03, 0.196, "SOCIAL & OSINT WIRES", color=SOC, fontsize=11, weight="bold")
    A.add_patch(plt.Rectangle((0.03, 0.188), 0.30, 0.0015, color=SOC))
    if tops:
        for i, t in enumerate(tops):
            colx = 0.03 + (i % 2) * 0.485
            yy = 0.176 - (i // 2) * 0.016
            A.text(colx, yy, "[%s] %s" % (t.get("src", ""), _clean(t.get("t", ""))[:58]), color=INK, fontsize=9)
    else:
        A.text(0.03, 0.174, "No fresh social items. Check proxy access and source coverage.", color=MUT2, fontsize=9)
    coverage = sp2.get("coverage", {})
    if coverage:
        A.text(0.97, 0.196, "coverage: " + " · ".join("%s %d" % (k, v) for k, v in coverage.items()),
               color=MUT2, fontsize=9, ha="right")

    for (bx, bw, btitle, bcol) in ((0.03, 0.40, "CROSS-ASSET ANALYSIS", MKT), (0.47, 0.25, "THEMES & SENTIMENT", SOC), (0.76, 0.21, "KEY NUMBERS", GEO)):
        px, py, pw = _panel(A, bx, 0.140, bw, 0.105, btitle, bcol)
        y = py
        if btitle == "CROSS-ASSET ANALYSIS":
            y = _block(A, px, y, pw, a["cross_asset"], 9.5, INK, 0.017, 3)
        elif btitle == "THEMES & SENTIMENT":
            top_themes = sorted(d["themes"].items(), key=lambda x: -x[1])[:3]
            mx = top_themes[0][1] if top_themes else 1
            for k, v in top_themes:
                A.text(px, y, _clean(DOMAIN_NAMES.get(k, k))[:12], color=MUT2, fontsize=9)
                A.add_patch(plt.Rectangle((px + pw * 0.45, y + 0.002), (pw * 0.4) * v / mx, 0.008, color=MKT))
                A.text(px + pw, y, str(v), color=INK, fontsize=9, ha="right"); y -= 0.015
            x = px
            for key, col in [("bullish", UP), ("neutral", MUT2), ("bearish", DN)]:
                w = (pw * 0.6) * rolls[key] / tot
                A.add_patch(plt.Rectangle((x, y - 0.002), w, 0.009, color=col)); x += w + 0.004
            A.text(px, y - .017, "News: bull %d / neutral %d / bear %d" % (rolls["bullish"], rolls["neutral"], rolls["bearish"]) if sum(rolls.values()) else "News sentiment unavailable", color=MUT2, fontsize=9)
        else:
            g0 = (pulse.get("gainers") or [{}])[0]; l0 = (pulse.get("losers") or [{}])[0]
            for lab, val, col in [("GAINER", "%s %+.2f%%" % (g0.get("t", "-"), g0.get("pct", 0)) if g0.get("t") else "-", UP),
                                  ("LOSER", "%s %+.2f%%" % (l0.get("t", "-"), l0.get("pct", 0)) if l0.get("t") else "-", DN),
                                  ("GOLD", pct(im.get("Gold", {}).get("pct")), UP if (im.get("Gold", {}).get("pct") or 0) > 0 else DN),
                                  ("10Y", _fmt_price(im.get("US 10Y Yield", {}).get("price"), "bond"), GEO)]:
                A.text(px, y, lab, color=MUT2, fontsize=9, weight="bold")
                A.text(px + pw, y, _clean(val), color=col, fontsize=9, ha="right", weight="bold"); y -= 0.014

    A.text(0.03, 0.020, "All charts computed from source snapshots | Tentative - machine-compiled, not investment advice", color=MUT2, fontsize=9)
    A.text(0.97, 0.020, "Page 2 of 2", color=MUT2, fontsize=9, ha="right")
    fig.savefig(path, facecolor=PAPER); plt.close(fig)

