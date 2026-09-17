"""Measured, accessible two-page Gazette rendering; no network or LLM calls."""
import re
from datetime import datetime, timezone
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

BG, FG, MUTED, BORDER = '#EDF2F6', '#172B40', '#536779', '#D8E2EA'
BLUE, UP, DOWN = '#185E88', '#087D72', '#B34246'
LAYOUT_AUDIT = []

def clean(value):
    return ' '.join(str(value or '').replace('$', r'\$').split())

class Page:
    def __init__(self, title, number):
        self.fig = plt.figure(figsize=(19.2, 10.8), dpi=200, facecolor=BG)
        self.ax = self.fig.add_axes([0, 0, 1, 1])
        self.ax.set(xlim=(0, 1), ylim=(0, 1)); self.ax.axis('off')
        self.fig.canvas.draw()
        self.renderer = self.fig.canvas.get_renderer()
        self.text(.03, .968, title, 23, weight='bold')
        self.text(.97, .966, datetime.now(timezone.utc).strftime('%d %b %Y  |  %H:%M UTC'), 11, ha='right', color=MUTED)
        self.text(.03, .027, 'AGGREGATEIT  /  Source snapshots; AI commentary is unverified. Not investment advice.', 10, color=MUTED)
        self.text(.97, .027, '%02d / 02' % number, 10, ha='right', color=MUTED)

    def text(self, x, y, text, size=12, **kw):
        return self.ax.text(x, y, clean(text), fontsize=size, color=kw.pop('color', FG),
                            va='top', fontfamily='DejaVu Sans', **kw)

    def wrap(self, text, width, size, weight='normal'):
        # Use actual glyph widths at the output DPI, not guessed characters.
        from matplotlib.font_manager import FontProperties
        prop = FontProperties(family='DejaVu Sans', size=size, weight=weight)
        limit = width * self.fig.bbox.width
        lines, line = [], ''
        for word in clean(text).split():
            candidate = (line + ' ' + word).strip()
            if self.renderer.get_text_width_height_descent(candidate, prop, False)[0] <= limit:
                line = candidate
            else:
                if line: lines.append(line)
                line = word
                # Long URLs/identifiers wrap without deleting characters.
                while self.renderer.get_text_width_height_descent(line, prop, False)[0] > limit:
                    n = len(line) - 1
                    while n > 1 and self.renderer.get_text_width_height_descent(line[:n], prop, False)[0] > limit:
                        n -= 1
                    lines.append(line[:n]); line = line[n:]
        if line: lines.append(line)
        return lines

    def card(self, x, top, width, height, title):
        self.ax.add_patch(plt.Rectangle((x, top-height), width, height, facecolor='white', edgecolor=BORDER, lw=.8))
        self.ax.add_patch(plt.Rectangle((x, top-.005), width, .005, facecolor=BLUE, edgecolor='none'))
        size = 12
        while size > 10 and len(self.wrap(title, width-.024, size, 'bold')) > 1:
            size -= .5
        self.text(x+.012, top-.018, title, size, weight='bold', color=BLUE)
        return Box(self, x+.012, top-.055, width-.024, top-height+.014)

    def save(self, path):
        self.fig.canvas.draw()
        self.fig.savefig(path, facecolor=BG); plt.close(self.fig)

class Box:
    def __init__(self, page, x, y, width, bottom):
        self.p, self.x, self.y, self.w, self.bottom = page, x, y, width, bottom

    def add(self, text, size=12, color=FG, weight='normal', gap=.010):
        if not text: return True
        lines = self.p.wrap(text, self.w, size, weight)
        step = size * 1.35 / (72 * 10.8)
        needed = len(lines) * step
        if self.y - needed < self.bottom: return False
        top = self.y
        for line in lines:
            self.p.text(self.x, self.y, line, size, color=color, weight=weight)
            self.y -= step
        LAYOUT_AUDIT.append((top, self.y, self.bottom))
        self.y -= gap
        return True

    def prose(self, text):
        # Fit complete paragraphs, then complete sentences. Never emit fragments.
        if self.add(text): return
        for sentence in re.split(r'(?<=[.!?])\s+', text or ''):
            if not self.add(sentence, gap=.006): break

    def events(self, rows):
        shown = 0
        for e in rows:
            title = e.get('title') or e.get('t') or ''
            meta = ' | '.join(str(v) for v in [e.get('severity'), e.get('source') or e.get('src')] if v)
            lines = self.p.wrap(title, self.w, 12, 'bold')
            ml = self.p.wrap(meta, self.w, 10)
            needed = len(lines)*12*1.35/777.6 + len(ml)*10*1.35/777.6 + .022
            if self.y-needed < self.bottom: break
            self.add(title, weight='bold', gap=.004)
            self.add(meta, 10, MUTED, gap=.012)
            shown += 1
        return shown

def pct(value):
    return 'Unavailable' if value is None else '%+.2f%%' % value

def freshness(ts):
    if not isinstance(ts, (int, float)) or ts <= 0: return 'unavailable'
    age = max(0, datetime.now(timezone.utc).timestamp()-ts)/60
    return '%dm old' % age

def render_p1(d, a, llm_ok, path):
    p = Page('THE AGGREGATE GAZETTE  /  Intelligence briefing', 1)
    pulse, events = d.get('pulse', {}), d.get('events', [])
    b = p.card(.03, .915, .615, .22, 'EDITORIAL SUMMARY')
    b.add(a.get('headline', 'Market and geopolitical update'), 18, weight='bold')
    b.prose(a.get('lead', ''))
    b = p.card(.66, .915, .31, .22, 'COVERAGE & FRESHNESS')
    b.add('%d events | %dh window | %d sources' % (len(events), d.get('event_window_h',24), len(d.get('sources_active',[]))), weight='bold')
    b.add('Market: %s | Macro: %s' % (freshness(pulse.get('updated')), freshness(d.get('macro',{}).get('updated'))), 11)
    b.add('Social: %s | Commentary: %s' % (freshness(d.get('social_pulse',{}).get('ts')), 'AI-generated' if llm_ok else 'fallback'), 11)
    b.add('Market session: ' + ('open' if pulse.get('session_open') else 'closed / previous snapshot'), 11)
    for x, title, key, rows in [(.03,'WORLD & GEOPOLITICS','geopol_read',d.get('geo_events',[])),
                                (.345,'EVENT WATCHLIST',None,events),
                                (.66,'MARKETS & ECONOMY','market_read',[])]:
        b=p.card(x,.675,.31,.325,title)
        if key: b.prose(a.get(key,''))
        if rows: b.events(rows)
        if title=='MARKETS & ECONOMY':
            for m in pulse.get('mega_caps',[])[:8]:
                if not b.add('%s  %s session' % (m.get('t',''),pct(m.get('pct'))),11): break
    b=p.card(.03,.33,.31,.265,'CHANGE & CROSS-ASSET CONTEXT')
    b.prose(a.get('delta',''))
    b.prose(a.get('cross_asset',''))
    b=p.card(.345,.33,.31,.265,'SOCIAL & OPEN-SOURCE WATCH')
    sp=d.get('social_pulse',{})
    counts=sp.get('coverage') or sp.get('counts') or {}
    b.add(' | '.join('%s: %s' % (k,v) for k,v in counts.items()) or 'No social coverage available.',10,MUTED)
    b.events(sp.get('top',[]))
    if not sp.get('top'): b.prose('No fresh social items were collected. This is missing coverage, not evidence of neutral sentiment.')
    b=p.card(.66,.33,.31,.265,'OUTLOOK & RISK WATCH')
    b.prose(a.get('outlook',''))
    b.add('KEY RISK',11,DOWN,weight='bold')
    b.prose(a.get('key_risk',''))
    themes=sorted(d.get('themes',{}).items(),key=lambda kv:-kv[1])
    if themes and b.y-b.bottom > .085:
        b.add('EVENT MIX',11,BLUE,weight='bold')
        b.add(' | '.join('%s: %s' % item for item in themes[:5]),11)
    p.save(path)

def chart(p, rect, title):
    x,top,w,h=rect
    p.card(x,top,w,h,title)
    ax=p.fig.add_axes([x+.058,top-h+.04,w-.082,h-.10])
    ax.set_facecolor('white'); ax.tick_params(labelsize=10,colors=MUTED)
    for spine in ax.spines.values(): spine.set_visible(False)
    ax.grid(axis='x',alpha=.16); ax.set_axisbelow(True)
    return ax

def bars(ax, names, vals):
    if not vals:
        ax.text(.5,.5,'No current observations',transform=ax.transAxes,ha='center',color=MUTED); return
    ax.barh(names[::-1],vals[::-1],color=[UP if v>=0 else DOWN for v in vals[::-1]],height=.62)
    ax.axvline(0,color=BORDER,lw=1)
    ax.margins(x=.25)
    for i,v in enumerate(vals[::-1]):
        ax.annotate(pct(v),(v,i),xytext=(4 if v>=0 else -4,0),textcoords='offset points',
                    va='center',ha='left' if v>=0 else 'right',fontsize=10,color=FG)

def render_p2(d, a, llm_ok, path):
    p=Page('MARKETS & DATA  /  Snapshot dashboard',2)
    pulse=d.get('pulse',{})
    mega=[m for m in pulse.get('mega_caps',[]) if m.get('pct') is not None]
    ax=chart(p,(.03,.915,.31,.405),'MEGA-CAPS / SESSION CHANGE (%)')
    bars(ax,[m['t'] for m in mega[:10]],[m['pct'] for m in mega[:10]])
    b=p.card(.03,.49,.31,.425,'MARKET BREADTH & ACTIVE MOVERS')
    if mega:
        up=sum(m['pct']>0 for m in mega); dn=sum(m['pct']<0 for m in mega)
        b.add('%d rising / %d falling / %d flat' % (up,dn,len(mega)-up-dn),14,weight='bold')
        b.add('Sample: %d tracked mega-caps, not the whole market.' % len(mega),10,MUTED)
    for label,rows in [('GAINERS',pulse.get('gainers',[])[:3]),('DECLINERS',pulse.get('losers',[])[:3])]:
        b.add(label,11,BLUE,weight='bold')
        for m in rows: b.add('%s   %s' % (m.get('t',''),pct(m.get('pct'))),12)
    b.add('Large percentage moves may involve small-cap stocks.',10,MUTED)
    b=p.card(.355,.915,.30,.85,'MACRO BOARD / LEVEL & DAILY CHANGE')
    instruments=d.get('macro',{}).get('instruments',[])
    for typ,label in [('index','CASH INDICES'),('index_future','INDEX FUTURES'),('commodity','COMMODITIES'),('forex','FOREIGN EXCHANGE'),('bond','TREASURY YIELDS')]:
        rows=[i for i in instruments if i.get('type')==typ]
        if not rows: continue
        b.add(label,11,BLUE,weight='bold',gap=.007)
        for row in rows[:5]:
            value=row.get('price')
            level='—' if value is None else ('%.2f%%' % value if typ=='bond' else '%.4f' % value if typ=='forex' else '%g' % value)
            b.add('%s   %s   (%s)' % (row.get('name',''),level,pct(row.get('pct'))),11,gap=.005)
        b.y-=.006
    missing=[label for typ,label in [('index_future','Index futures'),('index','cash indices')] if not any(i.get('type')==typ for i in instruments)]
    if missing: b.add('Unavailable: '+', '.join(missing)+'.',10,MUTED)
    b.add('Yield changes above are relative %, not basis points.',10,MUTED)
    ax=chart(p,(.67,.915,.30,.34),'US TREASURY CURVE / YIELD (%)')
    pts=[(n,d.get('curve_pts',{}).get(n)) for n in ['2Y','5Y','10Y','30Y'] if d.get('curve_pts',{}).get(n) is not None]
    if pts:
        ax.plot([n for n,v in pts],[v for n,v in pts],color=BLUE,lw=2,marker='o')
        ax.margins(y=.3)
        for n,v in pts: ax.annotate('%.2f%%'%v,(n,v),xytext=(0,10),textcoords='offset points',ha='center',fontsize=11)
    else: ax.text(.5,.5,'Yield data unavailable',transform=ax.transAxes,ha='center')
    b=p.card(.67,.555,.30,.49,'INTRADAY WATCH & REGIME')
    b.add('1-HOUR MOVERS / TRACKED LARGE CAPS',11,BLUE,weight='bold')
    rows=pulse.get('hour_movers',[])
    for m in rows[:5]: b.add('%s  %s (1h) | %s session' % (m.get('t',''),pct(m.get('hour_chg')),pct(m.get('pct'))),11)
    if not rows: b.prose('No qualifying hourly movers or insufficient snapshot history.')
    b.add('REGIME INDICATORS',11,BLUE,weight='bold')
    regime=d.get('regime',{})
    for key,label in [('vix','VIX'),('curve_2s10s','2Y–10Y spread'),('dxy','US dollar')]:
        if regime.get(key) is not None: b.add('%s: %s' % (label,regime[key]),12)
    b.add('DATA QUALITY',11,BLUE,weight='bold')
    b.add('Market '+freshness(pulse.get('updated'))+'; macro '+freshness(d.get('macro',{}).get('updated'))+'.',11)
    b.add('Unavailable feeds are not replaced with zero values. Price co-movement does not establish a news catalyst.',11,MUTED)
    p.save(path)
