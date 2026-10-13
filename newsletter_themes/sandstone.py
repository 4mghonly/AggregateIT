"""Sandstone Editorial: opt-in two-page 4K English Gazette renderer.

Offline presentation only. Uses the unchanged collected data and editorial
analysis; never invents prices, source confirmations or calendar events.
"""
import math
import re
import textwrap
from datetime import datetime
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle
from gazette_render import prepare, freshness, pct, _fmt_price, quality, edition_change, UAE_TZ

BG = "#F1EDE8"
PAPER = "#FFFCF8"
ESPRESSO = "#463830"
INK = "#352F2B"
MUTED = "#655C56"
COPPER = "#A96147"
LINE = "#DDD4CA"
GREEN = "#587260"
RED = "#B35E53"

def _clean(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()

def _safe(value, default="Unavailable"):
    t=_clean(value)
    return t if t else default

def _wrap(value,width,limit):
    lines=textwrap.wrap(_clean(value),width=width,break_long_words=True,break_on_hyphens=False)
    if len(lines)>limit:
        lines=lines[:limit]
        lines[-1]=lines[-1].rstrip(" .,:")+" ..."
    return lines

def _canvas(section,part,data):
    fig=plt.figure(figsize=(19.2,10.8),dpi=200,facecolor=BG)
    A=fig.add_axes([0,0,1,1]);A.set_xlim(0,1);A.set_ylim(0,1);A.axis("off")
    A.add_patch(Rectangle((0,.86),1,.14,color=ESPRESSO,lw=0))
    A.text(.035,.960,"AGGREGATEIT",fontsize=24,weight="bold",color=PAPER,va="center")
    A.text(.035,.909,section,fontsize=25,weight="bold",family="serif",color=PAPER,va="center")
    A.text(.965,.960,"GLOBAL NEWS & MARKETS",fontsize=12,ha="right",color="#E3C7AF",weight="bold")
    now=datetime.now(UAE_TZ).strftime("%d %b %Y  |  %H:%M UAE")
    A.text(.965,.911,now,fontsize=11.5,ha="right",color="#ECE3D9")
    A.add_patch(Rectangle((0,.858),1,.004,color=COPPER,lw=0))
    A.text(.035,.025,"AGGREGATEIT  /  SANDSTONE EDITORIAL",fontsize=10,color=MUTED,weight="bold")
    A.text(.965,.025,f"PAGE {part}/2  |  Source-attributed reporting  |  {'SYNTHETIC SAMPLE' if data.get('sample') else 'LIVE INPUT'}",fontsize=9,ha="right",color=MUTED)
    return fig,A

def _card(A,x,y,w,h,title=None,accent=COPPER):
    A.add_patch(FancyBboxPatch((x,y),w,h,boxstyle="round,pad=0.003,rounding_size=0.013",linewidth=.8,edgecolor=LINE,facecolor=PAPER))
    if title:
        A.text(x+.016,y+h-.039,title.upper(),fontsize=11.5,color=INK,weight="bold")
        A.add_patch(Rectangle((x+.015,y+h-.057),w-.03,.002,color=accent,lw=0))
        return y+h-.079
    return y+h-.03

def _paragraph(A,value,x,y,width=50,limit=4,size=12,lead=.028,color=INK,bold=False):
    for line in _wrap(value,width,limit):
        A.text(x,y,line,fontsize=size,color=color,weight="bold" if bold else "normal",va="top")
        y-=lead
    return y

def _source(e):
    return _safe(e.get("source"),"Source not recorded")

def _events(d,number=5):
    seen=set()
    for e in d.get("events",[]):
        title=_clean(e.get("title"))
        key=title.casefold()
        if not key or key in seen: continue
        seen.add(key)
        yield e
        if len(seen)>=number: break

def _figsave(fig,path):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    fig.savefig(path,dpi=200,facecolor=fig.get_facecolor(),pad_inches=0)
    plt.close(fig)

def render_p1(data, analysis, llm_ok, path):
    d=prepare(data); a=analysis or {}
    fig,A=_canvas("The Daily Briefing",1,d)
    # Leading editorial overview, with the original analysis retained rather
    # than replaced by unverified photo captions or generated stories.
    y=_card(A,.035,.48,.605,.34,"Lead development")
    y=_paragraph(A,_safe(a.get("headline"),"No editorial headline available"),.055,y,width=48,limit=2,size=23,lead=.048,bold=True)
    y-=.015
    _paragraph(A,_safe(a.get("lead"),"Editorial context unavailable"),.055,y,width=79,limit=4,size=12.8,lead=.031)
    A.text(.056,.497,"Editorial analysis  |  "+("LLM route confirmed" if llm_ok else "Fallback analysis / degraded"),fontsize=9.5,color=MUTED)
    y=_card(A,.665,.48,.300,.34,"Markets at a glance")
    macro=d.get("macro",{}); inst=macro.get("instruments",[])
    for i,item in enumerate(inst[:5]):
        yy=y-i*.051
        name=_safe(item.get("name"),"-")[:23]
        val=_fmt_price(item.get("price"),item.get("type"))
        change=pct(item.get("pct"))
        A.text(.685,yy,name,fontsize=11.8,color=INK,va="top")
        A.text(.852,yy,val,fontsize=11,ha="right",color=MUTED,va="top")
        A.text(.943,yy,change,fontsize=11,ha="right",color=GREEN if (item.get("pct") or 0)>0 else RED if (item.get("pct") or 0)<0 else MUTED,va="top",weight="bold")
    if not inst: A.text(.687,y,"No verified market snapshot",fontsize=12,color=MUTED)
    A.text(.685,.493,"Snapshot age: "+freshness(macro.get("updated")),fontsize=9,color=MUTED)

    # Four unmistakable reading cues, rather than repetitive news cards.
    cues=[("WORLD",str(len(d.get("events") or []))+" tracked events"),
          ("MARKETS", "Updated "+freshness(macro.get("updated"))),
          ("SIGNALS",str(len(d.get("social_pulse",{}).get("top") or []))+" social items"),
          ("WATCH",str(d.get("event_window_h",24))+"h evidence window")]
    for i,(title,sub) in enumerate(cues):
        x=.035+i*.233
        _card(A,x,.384,.218,.074)
        A.text(x+.014,.427,title,fontsize=11.2,weight="bold",color=COPPER)
        A.text(x+.014,.399,sub[:32],fontsize=10,color=INK)

    y=_card(A,.035,.070,.605,.294,"Leading source-reported headlines")
    for i,e in enumerate(_events(d,5)):
        yy=y-i*.052
        if yy<.09: break
        A.text(.056,yy,f"{i+1:02d}",fontsize=13.5,color=COPPER,weight="bold",va="top")
        _paragraph(A,e.get("title"),.103,yy,width=62,limit=1,size=12.4,lead=.017,bold=True)
        A.text(.104,yy-.024,_source(e)[:44]+"   |   "+freshness(e.get("ts")),fontsize=9.5,color=MUTED)
    _card(A,.665,.237,.300,.128,"What changed")
    _paragraph(A,_safe(a.get("delta"),edition_change(d)),.683,.280,width=45,limit=2,size=10.7,lead=.024)
    _card(A,.665,.070,.300,.146,"Social and OSINT")
    _paragraph(A,_safe(a.get("social_read"),"Social coverage unavailable"),.683,.146,width=45,limit=3,size=10.6,lead=.024)
    _figsave(fig,path)

def render_p2(data,analysis,llm_ok,path):
    d=prepare(data);a=analysis or {}
    fig,A=_canvas("Markets, Signals & Outlook",2,d)
    macro=d.get("macro",{}); inst=macro.get("instruments") or []
    y=_card(A,.035,.41,.60,.412,"Market instruments and session changes")
    groups={"index":[],"index_future":[],"commodity":[],"forex":[],"bond":[]}
    for item in inst:
        k=item.get("type")
        if k in groups: groups[k].append(item)
    row=0
    for title,key in [("INDICES","index"),("COMMODITIES","commodity"),("FOREX","forex"),("RATES","bond")]:
        if row>=12: break
        A.text(.055,y-row*.029,title,fontsize=9.5,color=COPPER,weight="bold");row+=1
        for item in groups[key][:2]:
            if row>=12: break
            yy=y-row*.029
            A.text(.064,yy,_safe(item.get("name"),"-")[:25],fontsize=10.4,color=INK)
            A.text(.455,yy,_fmt_price(item.get("price"),item.get("type")),fontsize=10.4,ha="right",color=MUTED)
            ch=item.get("pct")
            A.text(.612,yy,pct(ch),fontsize=10.4,ha="right",color=GREEN if (ch or 0)>0 else RED if (ch or 0)<0 else MUTED,weight="bold")
            row+=1
    if not inst:A.text(.056,.66,"Market data unavailable; no prices inferred.",fontsize=12,color=MUTED)
    A.text(.056,.431,"Price and change fields are shown only when present in the input snapshot.",fontsize=9,color=MUTED)

    y=_card(A,.655,.41,.31,.412,"Ticker activity")
    mega=d.get("pulse",{}).get("mega_caps") or []
    for i,m in enumerate(mega[:8]):
        yy=y-i*.041
        A.text(.675,yy,_safe(m.get("t"),"-")[:12],fontsize=12,color=INK,weight="bold")
        A.text(.942,yy,pct(m.get("pct")),ha="right",fontsize=11.2,
               color=GREEN if (m.get("pct") or 0)>0 else RED if (m.get("pct") or 0)<0 else MUTED)
    if not mega:A.text(.677,y,"Ticker snapshot unavailable",fontsize=11,color=MUTED)
    y=_card(A,.035,.071,.43,.30,"Market drivers")
    _paragraph(A,_safe(a.get("market_read"),"Market interpretation unavailable"),.055,y,width=65,limit=6,size=12,lead=.033)
    y=_card(A,.49,.071,.475,.30,"Analysis and watchlist")
    y=_paragraph(A,_safe(a.get("cross_asset"),"Cross-asset analysis unavailable"),.512,y,width=74,limit=3,size=11.7,lead=.027)
    y-=.015
    y=_paragraph(A,_safe(a.get("outlook"),"No outlook available"),.512,y,width=74,limit=3,size=11.7,lead=.027)
    A.text(.512,.092,"Key risk: "+_safe(a.get("key_risk"))[:103],fontsize=10.2,color=COPPER,weight="bold")
    # No fabricated options chains: the current collector does not guarantee
    # strike/expiry/volume rows, so omit that module until such data exist.
    A.text(.965,.839,"Data quality: market "+freshness(macro.get("updated"))+
           "  |  social "+freshness(d.get("social_pulse",{}).get("ts")),fontsize=9.5,ha="right",color=MUTED)
    _figsave(fig,path)
