"""Clean evidence-first two-page English V2 held edition. No market placeholders."""
from __future__ import annotations
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont

W,H=3840,2160
BG="#F5F2EC";INK="#20333B";MUTED="#596970";ACCENT="#A16B45";PANEL="#FFFFFF";BORDER="#D7D0C5"

def _font(size,bold=False):
    path=("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else
          "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    return ImageFont.truetype(path,size)

def _lines(draw,text,font,width):
    lines=[];line=""
    for word in str(text).split():
        candidate=(line+" "+word).strip()
        if line and draw.textbbox((0,0),candidate,font=font)[2]>width:
            lines.append(line);line=word
        else:line=candidate
    if line:lines.append(line)
    return lines

def _text(draw,text,x,y,width,size=34,bold=False,color=INK,max_lines=4):
    font=_font(size,bold)
    lines=_lines(draw,text,font,width)
    if len(lines)>max_lines:
        lines=lines[:max_lines]
        lines[-1]=lines[-1].rstrip(" .")+"…"
    for line in lines:
        draw.text((x,y),line,font=font,fill=color)
        y+=int(size*1.42)
    return y

def render_english_held(plan,output_dir):
    if plan.get("product")!="english" or not isinstance(plan.get("items"),list):
        raise ValueError("english_editorial_plan_required")
    items=plan["items"]
    if not items:raise ValueError("empty_english_edition")
    out=Path(output_dir);out.mkdir(parents=True,exist_ok=True)
    midpoint=(len(items)+1)//2
    pages=[]
    for page,stories in enumerate((items[:midpoint],items[midpoint:]),1):
        im=Image.new("RGB",(W,H),BG);d=ImageDraw.Draw(im)
        d.rectangle((0,0,W,18),fill=INK)
        d.text((140,95),"AGGREGATEIT",font=_font(64,True),fill=INK)
        d.text((140,205),"WORLD & STRATEGIC INTELLIGENCE",font=_font(36,True),fill=ACCENT)
        d.text((W-760,110),f"EDITION {page} / 2",font=_font(35,True),fill=MUTED)
        d.line((140,305,W-140,305),fill=BORDER,width=3)
        if stories:
            top=360;gap=30
            height=min(520,(1660-gap*(len(stories)-1))//len(stories))
            for i,story in enumerate(stories):
                y=top+i*(height+gap)
                d.rounded_rectangle((140,y,W-140,y+height),radius=22,fill=PANEL,outline=BORDER,width=3)
                evidence=story.get("evidence") or {}
                label=(str(story.get("region","global")).replace("_"," ").upper()+"  /  "+
                       str(story.get("topic","geopolitics")).upper())
                _text(d,label,195,y+32,W-390,26,True,ACCENT,1)
                quote=str(evidence.get("quote") or "").strip()
                _text(d,quote,195,y+100,W-390,43,True,INK,max_lines=5)
                source=str(evidence.get("source_id") or "source")
                url=str(evidence.get("source_url") or "")
                _text(d,"SOURCE  "+source+"   |   "+url,195,y+height-90,W-390,24,False,MUTED,2)
        else:
            _text(d,"No additional admitted developments in this edition.",
                  190,450,W-380,46,False,MUTED,3)
        d.line((140,2070,W-140,2070),fill=BORDER,width=2)
        _text(d,"Publisher-attributed excerpts; independent factual verification not established.",
              140,2090,W-280,25,False,MUTED,1)
        target=out/f"english-no-post-{page}.png"
        im.save(target,format="PNG",optimize=True)
        pages.append(target)
    return pages
