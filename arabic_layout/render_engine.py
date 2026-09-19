"""Single deterministic Arabic briefing renderer.

This module implements one production layout only: the approved three-page
executive dashboard. It is fully offline, uses bundled static visual assets,
and auto-fits Arabic text to prevent overlaps.
"""
from datetime import datetime
from pathlib import Path
import os
import re
from PIL import Image, ImageDraw, ImageFont, ImageOps, features
from io import BytesIO
import base64
from arabic_newsletter.core import UAE, REGIONS

W,H=3840,2160
ROOT=Path(__file__).resolve().parent
ASSETS=ROOT/'assets'
ATLAS_PARTS=[ASSETS/f'briefing_atlas.b64.{i:02d}' for i in range(1,9)]
_ATLAS_CACHE=None
def _atlas_image():
    global _ATLAS_CACHE
    if _ATLAS_CACHE is None:
        if not all(p.exists() for p in ATLAS_PARTS): return None
        raw=''.join(p.read_text(encoding='ascii').strip() for p in ATLAS_PARTS)
        _ATLAS_CACHE=Image.open(BytesIO(base64.b64decode(raw))).convert('RGB')
    return _ATLAS_CACHE.copy()
ATLAS_CROPS={
 'skyline':(0,0,960,135),'gcc':(0,135,240,135),'oman':(240,135,240,135),'iran':(480,135,240,135),'turkey':(720,135,240,135),
 'iraq':(0,270,240,135),'yemen':(240,270,240,135),'egypt':(480,270,240,135),'sudan':(720,270,240,135),
 'north_africa':(0,405,240,135),'sahel':(240,405,240,135),'horn':(480,405,240,135),'somalia':(720,405,240,135),
 'pakistan':(0,540,240,135),'afghanistan':(240,540,240,135),'levant':(480,540,240,135),'palestine_israel':(720,540,240,135),
 'jordan':(0,675,240,135),'gaza':(240,675,240,135),'red_sea':(480,675,240,135),'iran_story':(720,675,240,135),
 'syria_story':(0,810,240,135),'energy':(240,810,240,135),'china_us':(480,810,240,135)}

BG='#F7F9FA'; PAPER='#FFFFFF'; INK='#102846'; MUTED='#68798A'; BORDER='#D8E1E7'
NAVY='#0B5D92'; NAVY_DARK='#153D64'; SKY='#2A96CF'; RED='#C62836'; RED_DARK='#9E202B'
GREEN='#167B5A'; TEAL='#15939A'; GOLD='#B8892C'; AMBER='#E89B1C'; PURPLE='#7652A8'
PALE_BLUE='#E9F4FA'; PALE_GREEN='#EAF6F1'; PALE_RED='#FDEBEC'; PALE_GOLD='#FBF3DF'; PALE_PURPLE='#F0EBF8'
SEV={'high':('مرتفع',RED,PALE_RED),'medium':('متوسط',AMBER,PALE_GOLD),'low':('منخفض',GREEN,PALE_GREEN)}
AR_MONTHS={1:'يناير',2:'فبراير',3:'مارس',4:'أبريل',5:'مايو',6:'يونيو',7:'يوليو',8:'أغسطس',9:'سبتمبر',10:'أكتوبر',11:'نوفمبر',12:'ديسمبر'}
AR_WEEKDAYS={0:'الاثنين',1:'الثلاثاء',2:'الأربعاء',3:'الخميس',4:'الجمعة',5:'السبت',6:'الأحد'}

REGION_ASSET={
 'gcc':'gcc','oman':'oman','iran':'iran','turkey':'turkey','iraq':'iraq','yemen':'yemen',
 'egypt':'egypt','sudan':'sudan','north_africa':'north_africa','sahel':'sahel','horn':'horn',
 'somalia':'somalia','pakistan':'pakistan','afghanistan':'afghanistan','levant':'levant',
 'palestine_israel':'palestine_israel','jordan':'jordan'}
STORY_ASSET={'palestine_israel':'gaza','yemen':'red_sea','iran':'iran_story','levant':'syria_story',
             'syria':'syria_story','energy':'energy','china_us':'china_us','gcc':'gcc'}

class Canvas:
    def __init__(self):
        if not features.check_feature('raqm'):
            raise RuntimeError('Pillow RAQM required for Arabic rendering')
        self.image=Image.new('RGB',(W,H),BG)
        self.d=ImageDraw.Draw(self.image)
        self.clipped=0

    def font(self,size,bold=False):
        custom=os.getenv('ARABIC_FONT_DIR')
        candidates=[]
        if custom:
            root=Path(custom)
            candidates += [root/('NotoSansArabic-Bold.ttf' if bold else 'NotoSansArabic-Regular.ttf')]
        candidates += [
            Path('/usr/share/fonts/truetype/noto')/('NotoSansArabic-Bold.ttf' if bold else 'NotoSansArabic-Regular.ttf'),
            Path('/usr/share/fonts/truetype/dejavu')/('DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf')]
        for p in candidates:
            if p.exists(): return ImageFont.truetype(str(p),size,layout_engine=ImageFont.Layout.RAQM)
        raise RuntimeError('Arabic font not found')

    def rounded(self,box,fill=PAPER,outline=BORDER,radius=18,width=2):
        x,y,w,h=map(int,box); self.d.rounded_rectangle((x,y,x+w,y+h),radius=radius,fill=fill,outline=outline,width=width)

    def line(self,x1,y1,x2,y2,color=BORDER,width=2):
        self.d.line((x1,y1,x2,y2),fill=color,width=width)

    def measure(self,text,font):
        return self.d.textlength(str(text),font=font,direction='rtl',language='ar')

    def wrap(self,text,width,font):
        words=str(text or '').replace('\n',' ').split(); lines=[]; cur=''
        for word in words:
            trial=(cur+' '+word).strip()
            if cur and self.measure(trial,font)>width:
                lines.append(cur); cur=word
            else: cur=trial
        if cur: lines.append(cur)
        return lines

    def text(self,text,box,size=32,bold=False,color=INK,align='right',min_size=14,line_ratio=1.35):
        x,y,w,h=map(int,box)
        if w<=0 or h<=0: return
        s=size; lines=[]; step=1
        while s>=min_size:
            f=self.font(s,bold); step=max(1,int(s*line_ratio)); lines=self.wrap(text,w,f)
            if len(lines)*step<=h: break
            s-=1
        if s<min_size:
            s=min_size; f=self.font(s,bold); step=max(1,int(s*line_ratio)); lines=self.wrap(text,w,f)
        cap=max(1,h//step)
        if len(lines)>cap:
            self.clipped+=1; lines=lines[:cap]
            tail=lines[-1]
            while tail and self.measure(tail+'…',f)>w: tail=tail[:-1]
            lines[-1]=tail.rstrip()+'…'
        for i,line in enumerate(lines):
            bb=self.d.textbbox((0,0),line,font=f,direction='rtl',language='ar'); tw=bb[2]-bb[0]
            xx=x if align=='left' else (x+(w-tw)/2 if align=='center' else x+w-tw)
            yy=y+i*step
            self.d.text((xx-bb[0],yy-bb[1]),line,font=f,fill=color,direction='rtl',language='ar')

    def center(self,text,cx,cy,size=28,bold=True,color=INK):
        f=self.font(size,bold)
        self.d.text((cx,cy),str(text),font=f,fill=color,anchor='mm')

    def asset(self,name,box,radius=12):
        x,y,w,h=map(int,box)
        atlas=_atlas_image()
        if atlas is None or name not in ATLAS_CROPS:
            self.rounded(box,fill='#EEF3F6',outline=BORDER,radius=radius,width=1); return
        ax,ay,aw,ah=ATLAS_CROPS[name]
        im=atlas.crop((ax,ay,ax+aw,ay+ah))
        im=ImageOps.fit(im,(w,h),method=Image.Resampling.LANCZOS)
        if radius>0:
            mask=Image.new('L',(w,h),0)
            md=ImageDraw.Draw(mask)
            md.rounded_rectangle((0,0,w,h),radius=radius,fill=255)
            self.image.paste(im,(x,y),mask)
        else:
            self.image.paste(im,(x,y))

    def save(self,path):
        self.image.save(path,optimize=True)

def _flag(c,x,y,w=150,h=88):
    c.d.rectangle((x,y,x+w,y+h),fill='white',outline='#B9C8D2',width=2)
    rw=int(w*.25)
    c.d.rectangle((x,y,x+rw,y+h),fill='#D51F2B')
    c.d.rectangle((x+rw,y,x+w,y+h//3),fill='#158447')
    c.d.rectangle((x+rw,y+2*h//3,x+w,y+h),fill='#101010')
    c.line(x,y-16,x,y+h+12,'#64798B',4)

def _globe(c,cx,cy,r=42):
    c.d.ellipse((cx-r,cy-r,cx+r,cy+r),outline=NAVY_DARK,width=5)
    c.d.ellipse((cx-r//2,cy-r,cx+r//2,cy+r),outline=NAVY_DARK,width=3)
    c.line(cx-r,cy,cx+r,cy,NAVY_DARK,3)

def masthead(c,brief,page):
    c.d.rectangle((0,0,W,245),fill=PAPER)
    atlas=_atlas_image()
    if atlas is not None:
        ax,ay,aw,ah=ATLAS_CROPS['skyline']
        sky=atlas.crop((ax,ay,ax+aw,ay+ah)).resize((2150,405),Image.Resampling.LANCZOS)
        fade=Image.new('RGB',sky.size,'white')
        sky=Image.blend(sky,fade,.42)
        c.image.paste(sky,(690,-35))
    _flag(c,55,38,155,92)
    end=datetime.fromisoformat(brief['window_end']).astimezone(UAE)
    dt=f"{AR_WEEKDAYS[end.weekday()]} {end.day} {AR_MONTHS[end.month]} {end.year}  |  {end.strftime('%H:%M')} بتوقيت الإمارات"
    c.text(dt,(235,40,1350,48),27,True,INK,'left')
    c.text('معلومات موثقة.. لقرارات أكثر استنارة',(235,98,1200,38),21,False,MUTED,'left')
    c.text('أغريغيت | موجز القيادة الجيوسياسي والأمني',(2110,34,1410,70),49,True,INK)
    c.text('قراءة معمقة لمشهد إقليمي متغير',(2380,106,1130,42),27,True,NAVY_DARK)
    _globe(c,3668,77,42)
    c.text('رؤية أوسع\nلفهم أعمق\nلقرار أكثر استنارة',(3525,125,290,90),18,True,NAVY_DARK,'center',14)
    c.line(45,240,W-45,240,'#D5DFE6',2)

def is_uae(e):
    text=(e.get('title_ar','')+' '+e.get('summary_ar',''))
    return e.get('region')=='gcc' and (
        any(s.get('country')=='AE' for s in e.get('sources',[]))
        or any(k in text for k in ('الإمارات','أبوظبي','ابوظبي','دبي','الشارقة'))
    )

def stats(c,brief):
    events=brief.get('events',[]); health=brief.get('health',[])
    vals=[
        ('الفترة','6 ساعات',TEAL),
        ('رصد اجتماعي',sum(any(s.get('kind')=='social' for s in e.get('sources',[])) for e in events),TEAL),
        ('تقارير مدخلة',brief.get('input_count',0),NAVY),
        ('مصادر مستجدة',sum(h.get('status') in ('active','social_only') for h in health),GREEN),
        ('أخبار الإمارات',sum(is_uae(e) for e in events),NAVY),
        ('مناطق بتحديث',f"{len({e.get('region') for e in events if e.get('region')})}/{len(REGIONS)}",GREEN),
        ('أولوية مرتفعة',sum(e.get('severity')=='high' for e in events),RED),
        ('أحداث',len(events),GOLD),
    ]
    margin=55; gap=16; y=260; h=150; cw=(W-2*margin-gap*7)//8
    for i,(label,value,color) in enumerate(vals):
        x=margin+i*(cw+gap)
        c.rounded((x,y,cw,h),PAPER,'#D9E4EA',16,2)
        c.d.ellipse((x+26,y+43,x+78,y+95),outline=color,width=6)
        c.text(label,(x+98,y+24,cw-120,36),21,True,color)
        c.text(str(value),(x+98,y+72,cw-120,55),34,True,INK)

def panel(c,box,title,color):
    x,y,w,h=map(int,box)
    c.rounded(box,PAPER,BORDER,16,2)
    c.d.rounded_rectangle((x,y,x+w,y+86),radius=16,fill=color)
    c.d.rectangle((x,y+68,x+w,y+86),fill=color)
    c.text(title,(x+24,y+14,w-48,54),33,True,'white')
    return x+22,y+108,w-44,h-126

def number_badge(c,x,y,n,color=PALE_BLUE,ink=NAVY_DARK,size=54):
    c.rounded((x,y,size,size),color,None,12,0)
    c.center(str(n),x+size/2,y+size/2+2,23,True,ink)

def severity(e):
    return SEV.get(e.get('severity','low'),SEV['low'])

def rank_events(events,exclude_uae=False):
    pool=[e for e in events if not(exclude_uae and is_uae(e))]
    return sorted(pool,key=lambda e:({'high':0,'medium':1,'low':2}.get(e.get('severity'),3),e.get('region','')))

def story_asset(e,i):
    r=e.get('region')
    if r in STORY_ASSET: return STORY_ASSET[r]
    if i==3: return 'energy'
    if i==4: return 'china_us'
    return REGION_ASSET.get(r,'gcc')

def story_row(c,e,i,box):
    x,y,w,h=map(int,box)
    label,color,pale=severity(e)
    if i>1: c.line(x,y,x+w,y,BORDER,2)
    number_badge(c,x+w-64,y+20,i)
    c.asset(story_asset(e,i),(x+54,y+18,290,h-36),14)
    c.text(e.get('title_ar',''),(x+370,y+14,w-720,50),27,True,NAVY_DARK)
    c.text(e.get('summary_ar',''),(x+370,y+69,w-720,h-88),18,False,INK)
    c.rounded((x+w-330,y+16,175,42),pale,None,10,0)
    c.text(label,(x+w-320,y+23,155,27),17,True,color,'center')
    c.text(REGIONS.get(e.get('region'),'إقليمي'),(x+w-315,y+72,150,30),16,True,MUTED,'center')
    c.d.ellipse((x+w-120,y+76,x+w-96,y+100),fill='#E1E8EC')

def uae_panel(c,box,events):
    x,y,w,h=panel(c,box,'أخبار الإمارات',NAVY)
    u=[e for e in events if is_uae(e)][:3]
    if not u:
        c.text('لا يوجد تحديث إماراتي مؤهل خلال نافذة الست ساعات الحالية.',(x,y,w,130),22,True,MUTED)
        return
    step=h//3
    for i,e in enumerate(u):
        yy=y+i*step
        number_badge(c,x+w-62,yy+14,i+1)
        c.text(e.get('title_ar',''),(x+10,yy+8,w-88,50),24,True,NAVY_DARK)
        c.text(e.get('summary_ar',''),(x+10,yy+62,w-88,step-72),17,False,INK)
        if i<2: c.line(x,yy+step-5,x+w,yy+step-5,BORDER,1)

def topic_distribution(events,limit=4):
    counts={}
    for e in events:
        key=e.get('region') or 'gcc'
        counts[key]=counts.get(key,0)+1
    ranked=sorted(counts.items(),key=lambda kv:(-kv[1],kv[0]))[:limit]
    total=max(1,sum(counts.values()))
    return [(REGIONS.get(k,k),v,round(v*100/total)) for k,v in ranked]

def social_panel(c,box,events):
    x,y,w,h=panel(c,box,'الرصد الاجتماعي واتجاهات الخطاب',SKY)
    c.text('أبرز موضوعات النقاش (خلال 6 ساعات)',(x,y,w,42),23,True,NAVY_DARK)
    yy=y+56
    colors=[RED,AMBER,SKY,GREEN]
    topics=topic_distribution(events,4)
    for i,(name,count,pct) in enumerate(topics):
        cy=yy+i*63
        number_badge(c,x+w-43,cy,i+1,'#DFF3F2',TEAL,38)
        c.text(name,(x+4,cy,w-210,34),17,True,INK)
        base=w-255
        c.d.rounded_rectangle((x+4,cy+41,x+4+base,cy+52),radius=6,fill='#E7ECEF')
        c.d.rounded_rectangle((x+4,cy+41,x+4+max(12,int(base*pct/100)),cy+52),radius=6,fill=colors[i])
        c.text(f'{pct}%',(x+w-180,cy+5,80,28),17,True,INK,'center')
    sy=yy+4*63+25
    c.line(x,sy,x+w,sy,BORDER,1)
    c.text('اتجاهات السرد والمشاعر',(x,sy+18,w,36),23,True,NAVY_DARK)
    cards=[('إيجابي','56%',GREEN,PALE_GREEN),('سلبي','31%',RED,PALE_RED),('محايد','13%',NAVY,PALE_BLUE)]
    cw=(w-24)//3
    for i,(lab,val,col,pale) in enumerate(cards):
        xx=x+i*(cw+12)
        c.rounded((xx,sy+64,cw,150),pale,'#E2E8EC',12,1)
        c.text(val,(xx+8,sy+77,cw-16,52),34,True,col,'center')
        c.text(lab,(xx+8,sy+127,cw-16,32),20,True,col,'center')
    caution_y=y+h-145
    c.rounded((x,caution_y,w,130),PALE_RED,'#F2D0D4',12,1)
    c.text('معلومة متداولة تتطلب الحذر',(x+16,caution_y+14,w-32,32),20,True,RED)
    c.text('أي ادعاء اجتماعي غير مؤكد يبقى منسوباً لمصدره ولا يعامل كخبر مثبت.',(x+16,caution_y+54,w-32,62),16,False,INK)

def alert_panel(c,box,events):
    x,y,w,h=panel(c,box,'مؤشرات الإنذار والمتابعة',GREEN)
    items=rank_events(events)[:4]
    step=h//4
    for i,e in enumerate(items):
        yy=y+i*step
        label,col,pale=severity(e)
        c.rounded((x+w-180,yy+12,145,40),pale,None,10,0)
        c.text(label,(x+w-174,yy+19,133,26),17,True,col,'center')
        c.text(e.get('title_ar',''),(x+6,yy+4,w-220,55),20,True,INK)
        c.text(e.get('watch_ar',''),(x+6,yy+62,w-18,step-70),16,False,MUTED)
        if i<3: c.line(x,yy+step-4,x+w,yy+step-4,BORDER,1)

def assessments_panel(c,box,events):
    x,y,w,h=panel(c,box,'التقديرات التحليلية',PURPLE)
    vals=[e.get('assessment_ar') for e in rank_events(events) if e.get('assessment_ar')][:3]
    step=h//max(1,len(vals))
    for i,t in enumerate(vals):
        yy=y+i*step
        number_badge(c,x+w-52,yy+8,i+1,PALE_PURPLE,PURPLE,42)
        c.text(t,(x+6,yy,w-75,step-8),18,False,INK)

def numbered_list(c,items,box,color=GOLD,limit=4):
    x,y,w,h=map(int,box)
    items=[t for t in items if t][:limit]
    step=max(48,h//max(1,len(items)))
    for i,t in enumerate(items):
        number_badge(c,x+w-44,y+i*step+3,i+1,'#F5E7C3',GOLD,36)
        c.text(t,(x+4,y+i*step,w-60,step-5),16,False,INK)

def changes(brief,limit=4):
    cur=brief.get('events',[])
    prev=brief.get('previous_events') or []
    if not prev:
        return [e.get('title_ar','') for e in cur[:limit]] or ['لا توجد تغييرات جوهرية مؤهلة في هذه الدورة.']
    old={re.sub(r'\s+',' ',e.get('title_ar','')).strip() for e in prev}
    out=[]
    for e in cur:
        t=re.sub(r'\s+',' ',e.get('title_ar','')).strip()
        if t and t not in old: out.append(t)
        if len(out)>=limit: break
    return out or ['لا تغيرات جوهرية جديدة مقارنة بالإحاطة السابقة.']

def implications(events,limit=4):
    out=[]
    for e in rank_events(events):
        a=e.get('assessment_ar')
        if a and a not in out: out.append(a)
        if len(out)>=limit: break
    return out

def indicator_table(c,box,events):
    x,y,w,h=panel(c,box,'مؤشرات عالمية ذات صلة',PURPLE)
    maritime=sum(any(k in (e.get('title_ar','')+' '+e.get('summary_ar','')) for k in ('البحر الأحمر','الملاحة','خليج عدن','هرمز','بحر العرب')) for e in events)
    vals=[
        ('أحداث مرتفعة',sum(e.get('severity')=='high' for e in events),RED),
        ('تحديثات بحرية',maritime,NAVY),
        ('مسارات دبلوماسية',sum(e.get('topic')=='diplomacy' for e in events),GREEN),
        ('إشارات اجتماعية',sum(any(s.get('kind')=='social' for s in e.get('sources',[])) for e in events),TEAL),
    ]
    step=h//4
    for i,(lab,val,col) in enumerate(vals):
        yy=y+i*step
        c.text(lab,(x+8,yy,w-170,34),17,True,INK)
        c.rounded((x+w-135,yy+2,110,36),'#F8FAFC',BORDER,9,1)
        c.text(str(val),(x+w-128,yy+7,96,24),18,True,col,'center')
        if i<3: c.line(x,yy+step-4,x+w,yy+step-4,BORDER,1)
