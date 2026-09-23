"""Pure-information Arabic policy briefing renderer.

No illustrative images, generated artwork, maps or decorative visual renders are
used. The design is typography-first, evidence-first and optimized for crisp
Discord viewing at 4K.
"""
from datetime import datetime
from pathlib import Path
import os, re
from PIL import Image, ImageDraw, ImageFont, features
from arabic_newsletter.core import UAE, REGIONS

W,H=3840,2160
BG='#F2F3F0'; PAPER='#FFFFFF'; INK='#111A20'; MUTED='#53606A'; BORDER='#C7CDC8'
COMMAND='#1F2C33'; OLIVE='#53604A'; SAND='#B3A073'; STEEL='#415A66'
ALERT='#8B3038'; AMBER='#9A672E'; TEAL='#3B6C6B'; BLUE='#3F6681'; PURPLE='#665875'
PALE_RED='#F6E7E8'; PALE_AMBER='#F4EEE4'; PALE_GREEN='#E9EFE8'; PALE_BLUE='#E8EFF3'
SEV={'high':('مرتفع',ALERT,PALE_RED),'medium':('متوسط',AMBER,PALE_AMBER),'low':('منخفض',OLIVE,PALE_GREEN)}
AR_MONTHS={1:'يناير',2:'فبراير',3:'مارس',4:'أبريل',5:'مايو',6:'يونيو',7:'يوليو',8:'أغسطس',9:'سبتمبر',10:'أكتوبر',11:'نوفمبر',12:'ديسمبر'}
AR_WEEKDAYS={0:'الاثنين',1:'الثلاثاء',2:'الأربعاء',3:'الخميس',4:'الجمعة',5:'السبت',6:'الأحد'}

REGION_COLORS={
 'gcc':'#8B343B','oman':'#A95358','iran':'#416B57','turkey':'#665875','iraq':'#8B6742',
 'yemen':'#A87344','egypt':'#4D6F78','sudan':'#7E4C52','north_africa':'#566B86',
 'sahel':'#3F6681','horn':'#4D7A7A','somalia':'#5F8BA7','pakistan':'#4C735E',
 'afghanistan':'#74675F','levant':'#6B5B78','palestine_israel':'#506477','jordan':'#846B46'
}

def sanitize_text(value):
    s=str(value or '')
    for bad in ('\ufffd','\u25a1','\u25a0','\ufeff','\u200e','\u200f'):
        s=s.replace(bad,'')
    s=s.replace('|','،').replace('—','،').replace('–','،')
    s=re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]','',s)
    return re.sub(r'\s+',' ',s).strip()

def compact(text,limit=170):
    text=sanitize_text(text)
    if len(text)<=limit: return text
    cut=max(text.rfind('،',0,limit),text.rfind('؛',0,limit),text.rfind('.',0,limit),text.rfind('؟',0,limit))
    if cut>limit*.55: return text[:cut+1]
    return text[:limit].rstrip()+'…'

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
            candidates.append(root/('NotoSansArabic-Bold.ttf' if bold else 'NotoSansArabic-Regular.ttf'))
        candidates += [
            Path('/usr/share/fonts/truetype/dejavu')/('DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf'),
            Path('/usr/share/fonts/truetype/noto')/('NotoSansArabic-Bold.ttf' if bold else 'NotoSansArabic-Regular.ttf')]
        for p in candidates:
            if p.exists(): return ImageFont.truetype(str(p),size,layout_engine=ImageFont.Layout.RAQM)
        raise RuntimeError('Arabic font not found')

    def rounded(self,box,fill=PAPER,outline=BORDER,radius=14,width=2):
        x,y,w,h=map(int,box)
        self.d.rounded_rectangle((x,y,x+w,y+h),radius=radius,fill=fill,outline=outline,width=width)

    def line(self,x1,y1,x2,y2,color=BORDER,width=2):
        self.d.line((x1,y1,x2,y2),fill=color,width=width)

    def measure(self,text,font):
        return self.d.textlength(str(text),font=font,direction='rtl',language='ar')

    def wrap(self,text,width,font):
        words=sanitize_text(text).split()
        lines=[]; cur=''
        for word in words:
            trial=(cur+' '+word).strip()
            if cur and self.measure(trial,font)>width:
                lines.append(cur); cur=word
            else: cur=trial
        if cur: lines.append(cur)
        return lines

    def text(self,text,box,size=32,bold=False,color=INK,align='right',min_size=19,line_ratio=1.35):
        x,y,w,h=map(int,box)
        text=sanitize_text(text)
        if not text or w<=0 or h<=0: return
        chosen=None
        for s in range(size,min_size-1,-1):
            f=self.font(s,bold); step=max(1,int(s*line_ratio)); lines=self.wrap(text,w,f)
            if len(lines)*step<=h:
                chosen=(f,step,lines); break
        if chosen is None:
            f=self.font(min_size,bold); step=max(1,int(min_size*line_ratio)); lines=self.wrap(text,w,f)
            cap=max(1,h//step)
            if len(lines)>cap:
                self.clipped+=1
                lines=lines[:cap]
                # End on a complete visual line rather than slicing through the box.
                lines[-1]=lines[-1].rstrip('،؛:')+'…'
            chosen=(f,step,lines)
        f,step,lines=chosen
        for i,line in enumerate(lines):
            bb=self.d.textbbox((0,0),line,font=f,direction='rtl',language='ar')
            tw=bb[2]-bb[0]
            xx=x if align=='left' else (x+(w-tw)/2 if align=='center' else x+w-tw)
            yy=y+i*step
            self.d.text((xx-bb[0],yy-bb[1]),line,font=f,fill=color,direction='rtl',language='ar')

    def center(self,text,cx,cy,size=28,bold=True,color=INK):
        f=self.font(size,bold)
        self.d.text((cx,cy),sanitize_text(text),font=f,fill=color,anchor='mm')

    def save(self,path):
        self.image.save(path,format='PNG',compress_level=2,dpi=(144,144))

def masthead(c,brief,page):
    end=datetime.fromisoformat(brief['window_end']).astimezone(UAE)
    morning=bool(brief.get('morning'))
    c.text('أغريغيت | الموجز الجيوسياسي والأمني',(2180,34,1500,58),48,True,INK)
    c.text('دليل موجز لصانع القرار، وقائع منسوبة وتحليل تقديري منفصل',(2180,101,1500,38),24,False,MUTED)
    dt=f"{AR_WEEKDAYS[end.weekday()]} {end.day} {AR_MONTHS[end.month]} {end.year}، {end.strftime('%H:%M')} بتوقيت الإمارات"
    c.text(dt,(80,42,1500,44),28,True,INK,'left')
    cycle='إحاطة صباحية موسعة، تغطية ليلية 12 ساعة' if morning else 'إحاطة دورية، نافذة 6 ساعات'
    c.text(cycle,(80,100,1500,34),22,False,MUTED,'left')
    c.line(70,165,W-70,165,'#8E8A82',2)


def stats(c,brief):
    events=brief.get('events',[])
    period='12 ساعة' if brief.get('morning') else '6 ساعات'
    coverage=brief.get('coverage') or {}
    vals=[
      ('نافذة التغطية',period,STEEL),
      ('أحداث مؤهلة',len(events),COMMAND),
      ('مصادر مستخدمة',coverage.get('event_source_count',0),OLIVE),
      ('مناطق مغطاة',f"{len({e.get('region') for e in events if e.get('region')})}/{len(REGIONS)}",BLUE),
    ]
    margin=55; gap=18; y=190; h=108; cw=(W-2*margin-gap*3)//4
    for i,(label,val,color) in enumerate(vals):
        x=margin+i*(cw+gap)
        c.rounded((x,y,cw,h),PAPER,BORDER,10,1)
        c.d.rectangle((x+cw-7,y+8,x+cw-2,y+h-8),fill=color)
        c.text(label,(x+24,y+18,cw-48,30),20,False,MUTED,'center')
        c.text(str(val),(x+24,y+51,cw-48,42),30,True,INK,'center')


def panel(c,box,title,color=COMMAND,subtitle=None):
    x,y,w,h=map(int,box)
    c.rounded(box,PAPER,BORDER,10,1)
    c.text(title,(x+22,y+14,w-44,44),31,True,color)
    c.line(x+18,y+66,x+w-18,y+66,color,2)
    header=82
    if subtitle:
        c.text(subtitle,(x+22,y+76,w-44,32),18,False,MUTED)
        header=118
    return x+24,y+header,w-48,h-header-24


def severity(e):
    return SEV.get(e.get('severity','low'),SEV['low'])

def is_uae(e):
    text=(e.get('title_ar','')+' '+e.get('summary_ar',''))
    return e.get('region')=='gcc' and (
        any(s.get('country')=='AE' for s in e.get('sources',[]))
        or any(k in text for k in ('الإمارات','أبوظبي','ابوظبي','دبي','الشارقة')))

def rank_events(events,exclude_uae=False):
    pool=[e for e in events if not(exclude_uae and is_uae(e))]
    return sorted(pool,key=lambda e:({'high':0,'medium':1,'low':2}.get(e.get('severity'),3),e.get('region','')))

def featured_events(events,limit=6,exclude_uae=False):
    out=[]; seen=set()
    for e in rank_events(events,exclude_uae):
        r=e.get('region')
        if r in seen: continue
        seen.add(r); out.append(e)
        if len(out)>=limit: break
    return out

def row_event(c,e,i,box):
    x,y,w,h=map(int,box); label,col,pale=severity(e)
    if i>1: c.line(x,y,x+w,y,BORDER,2)
    c.rounded((x+w-76,y+17,56,56),pale,None,10,0); c.center(str(i),x+w-48,y+45,24,True,col)
    c.rounded((x+4,y+17,180,44),REGION_COLORS.get(e.get('region'),STEEL),None,8,0)
    c.text(REGIONS.get(e.get('region'),'إقليمي'),(x+12,y+23,164,30),20,True,'#FFFFFF','center')
    c.text(compact(e.get('title_ar',''),105),(x+210,y+8,w-500,62),34,True,INK)
    c.text(compact(e.get('summary_ar',''),175),(x+210,y+74,w-250,h-88),27,False,INK)
    c.rounded((x+w-230,y+87,130,38),pale,None,8,0); c.text(label,(x+w-222,y+92,114,27),18,True,col,'center')

def changes(brief,limit=4):
    cur=brief.get('events',[]); prev=brief.get('previous_events') or []
    if not prev: return [e.get('title_ar','') for e in cur[:limit]]
    old={sanitize_text(e.get('title_ar','')) for e in prev}
    return [e.get('title_ar','') for e in cur if sanitize_text(e.get('title_ar','')) not in old][:limit]

def implications(events,limit=4):
    out=[]
    for e in rank_events(events):
        a=sanitize_text(e.get('assessment_ar',''))
        if a and a not in out: out.append(a)
        if len(out)>=limit: break
    return out

def list_block(c,items,box,color=COMMAND,size=25,limit=6):
    x,y,w,h=map(int,box); items=[sanitize_text(i) for i in items if sanitize_text(i)][:limit]
    if not items:
        c.text('لا توجد عناصر إضافية مؤهلة في هذه الدورة.',box,size,False,MUTED); return
    step=h//len(items)
    for i,item in enumerate(items):
        yy=y+i*step
        c.rounded((x+w-48,yy+4,38,38),color,None,8,0); c.center(str(i+1),x+w-29,yy+23,17,True,'#FFFFFF')
        c.text(item,(x+4,yy,w-66,step-6),size,False,INK,min_size=20)

LANGUAGE_LABELS={'ar':'العربية','en':'الإنجليزية','fa':'الفارسية','tr':'التركية','fr':'الفرنسية','ur':'الأردية','so':'الصومالية','unknown':'أخرى'}

def source_distribution(brief,limit=6):
    counts=(brief.get('coverage') or {}).get('event_source_languages') or {}
    total=max(1,sum(counts.values()))
    rows=sorted(counts.items(),key=lambda z:(-z[1],str(z[0])))[:limit]
    return [(LANGUAGE_LABELS.get(k,k),v,round(v*100/total)) for k,v in rows]
