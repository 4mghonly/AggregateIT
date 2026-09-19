"""Approved three-slide Arabic geopolitical briefing layout.

The first page follows the clean analytical-dashboard reference approved for Discord:
UAE updates and chatter at left, six detailed developments in the center, alert and
assessment panels at right; slide three is analytics-led with a compact maritime update.
All drawing is offline, deterministic, RTL-shaped, measured, and bounded.
"""
from datetime import datetime
from pathlib import Path
import os
import re
from PIL import Image, ImageDraw, ImageFont, features
from .core import UAE, REGIONS

W,H=3840,2160
BG='#F3F6F8'
PAPER='#FFFFFF'
INK='#142334'
MUTED='#667788'
BORDER='#D5DEE5'
NAVY='#143A5A'
NAVY2='#244F70'
RED='#A82C38'
BLUE='#2E6F9E'
GOLD='#A77828'
GREEN='#2E765C'
TEAL='#347F80'
PURPLE='#665A84'
PALE_BLUE='#EEF5F8'
PALE_GOLD='#F8F2E7'
PALE_GREEN='#EDF5F1'
PALE_RED='#F8ECEE'
SEVERITY={'high':('مرتفع',RED),'medium':('متوسط',GOLD),'low':('منخفض',GREEN)}
AR_MONTHS={1:'يناير',2:'فبراير',3:'مارس',4:'أبريل',5:'مايو',6:'يونيو',7:'يوليو',8:'أغسطس',9:'سبتمبر',10:'أكتوبر',11:'نوفمبر',12:'ديسمبر'}
AR_WEEKDAYS={0:'الاثنين',1:'الثلاثاء',2:'الأربعاء',3:'الخميس',4:'الجمعة',5:'السبت',6:'الأحد'}

class Canvas:
    def __init__(self):
        if not features.check_feature('raqm'):
            raise RuntimeError('Pillow RAQM required for correct Arabic shaping')
        self.image=Image.new('RGB',(W,H),BG)
        self.d=ImageDraw.Draw(self.image)
        self.boxes=[]
        self.truncated=0

    def font(self,size,bold=False):
        candidates=[]
        custom=os.getenv('ARABIC_FONT_DIR')
        if custom:
            root=Path(custom)
            candidates.extend([
                root/('NotoSansArabic-Bold.ttf' if bold else 'NotoSansArabic-Regular.ttf'),
                root/('DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf'),
            ])
        candidates.extend([
            Path('/usr/share/fonts/truetype/noto')/('NotoSansArabic-Bold.ttf' if bold else 'NotoSansArabic-Regular.ttf'),
            Path('/usr/share/fonts/truetype/dejavu')/('DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf'),
        ])
        for p in candidates:
            if p.exists():
                return ImageFont.truetype(str(p),size,layout_engine=ImageFont.Layout.RAQM)
        raise RuntimeError('No supported Arabic font found')

    def width(self,text,font):
        return self.d.textlength(str(text),font=font,direction='rtl',language='ar')

    def lines(self,text,width,font):
        words=str(text or '').replace('\n',' ').split()
        out=[]; line=''
        for word in words:
            probe=(line+' '+word).strip()
            if line and self.width(probe,font)>width:
                out.append(line); line=''
            while self.width(word,font)>width and len(word)>1:
                n=len(word)-1
                while n>1 and self.width(word[:n],font)>width:
                    n-=1
                if line:
                    out.append(line); line=''
                out.append(word[:n]); word=word[n:]
            line=(line+' '+word).strip()
        if line: out.append(line)
        return out

    def text(self,text,box,size=34,bold=False,color=INK,align='right',line_ratio=1.42):
        x,y,w,h=map(int,box)
        if w<=0 or h<=0: return y
        original=size
        # Prefer a modest font reduction over clipping when live text is longer.
        while size>=14:
            font=self.font(size,bold)
            step=max(1,round(size*line_ratio))
            lines=self.lines(text,w,font)
            capacity=max(0,h//step)
            if len(lines)<=capacity:
                break
            size-=1
        if size<14:
            size=14
            font=self.font(size,bold)
            step=max(1,round(size*line_ratio))
            lines=self.lines(text,w,font)
            capacity=max(0,h//step)
        if len(lines)>capacity:
            self.truncated+=1
            lines=lines[:capacity]
            if lines:
                tail=lines[-1]
                while tail and self.width(tail+'…',font)>w:
                    tail=tail[:-1]
                lines[-1]=tail.rstrip()+'…'
        for i,line in enumerate(lines):
            bounds=self.d.textbbox((0,0),line,font=font,direction='rtl',language='ar')
            tw=bounds[2]-bounds[0]; th=bounds[3]-bounds[1]
            if align=='center':
                xx=x+(w-tw)/2
            elif align=='left':
                xx=x
            else:
                xx=x+w-tw
            yy=y+i*step
            self.d.text((xx-bounds[0],yy-bounds[1]),line,font=font,fill=color,direction='rtl',language='ar')
            self.boxes.append((xx,yy,xx+tw,yy+th,x,y,x+w,y+h))
        return y+len(lines)*step

    def rounded(self,box,fill=PAPER,outline=BORDER,radius=22,width=2):
        x,y,w,h=map(int,box)
        self.d.rounded_rectangle((x,y,x+w,y+h),radius=radius,fill=fill,outline=outline,width=width)

    def shadow(self,box,offset=8,radius=24):
        x,y,w,h=map(int,box)
        self.d.rounded_rectangle((x+offset,y+offset,x+w+offset,y+h+offset),radius=radius,fill='#DCE6EC')

    def rule(self,x,y,w,color=BORDER,width=2):
        self.d.line((x,y,x+w,y),fill=color,width=width)

    def save(self,path):
        for left,top,right,bottom,x,y,x2,y2 in self.boxes:
            if left<x-2 or top<y-2 or right>x2+2 or bottom>y2+2:
                raise RuntimeError('Text exceeded its measured box')
        self.image.save(path,optimize=True)

def _skyline(c):
    c.d.rectangle((0,0,W,255),fill='#EEF5F9')
    base=218
    towers=[
        (80,146,48),(150,118,34),(205,160,56),(285,95,38),(355,132,60),
        (450,75,32),(520,125,62),(625,105,38),(720,142,62),(825,92,44),
        (925,128,68),(1030,63,34),(1120,120,50),(1215,144,62),(1320,102,40),
        (1420,128,60),(1510,85,34),(1600,138,70),(1710,110,42),(1810,145,64),
        (1920,82,34),(2015,128,58),(2115,55,38),(2200,140,68),(2310,95,44),
        (2410,132,60),(2515,72,34),(2610,120,52),(2710,142,66),(2815,105,38),
        (2910,134,58),(3015,90,34),(3110,137,62),(3215,112,44),(3310,143,66),
        (3420,99,38),(3510,132,58),(3615,115,42)
    ]
    for x,top,w in towers:
        c.d.rectangle((x,top,x+w,base),fill='#B7C8D5')
        c.d.rectangle((x+5,top+10,x+w-5,base),fill='#C8D6E0')
        c.d.line((x+w/2,top-22,x+w/2,top),fill='#9DB2C1',width=3)
    c.d.polygon([(1740,218),(1775,36),(1810,218)],fill='#A9BECF')
    c.d.line((1775,12,1775,48),fill='#829EAF',width=4)
    c.d.rectangle((0,218,W,255),fill='#D8E5EC')

def _flag(c,x,y,scale=1.0):
    w=int(145*scale); h=int(90*scale); red=int(37*scale)
    c.d.rectangle((x,y,x+w,y+h),fill='white',outline='#B9C7D1',width=2)
    c.d.rectangle((x,y,x+red,y+h),fill='#C91F2B')
    c.d.rectangle((x+red,y,x+w,y+h//3),fill='#128548')
    c.d.rectangle((x+red,y+h//3,x+w,y+2*h//3),fill='#FFFFFF')
    c.d.rectangle((x+red,y+2*h//3,x+w,y+h),fill='#111111')
    c.d.line((x,y-18,x,y+h+12),fill='#4E6678',width=max(2,int(4*scale)))

def _globe(c,cx,cy,r=40,color=NAVY):
    c.d.ellipse((cx-r,cy-r,cx+r,cy+r),outline=color,width=5)
    c.d.ellipse((cx-r//2,cy-r,cx+r//2,cy+r),outline=color,width=3)
    c.d.line((cx-r,cy,cx+r,cy),fill=color,width=3)
    c.d.arc((cx-r,cy-r//2,cx+r,cy+r//2),0,180,fill=color,width=3)
    c.d.arc((cx-r,cy-r//2,cx+r,cy+r//2),180,360,fill=color,width=3)

def masthead(c,brief,page,title):
    # Clean white masthead matching the approved analytical-dashboard reference.
    c.d.rectangle((0,0,W,155),fill=PAPER)
    _flag(c,58,34,0.72)
    end=datetime.fromisoformat(brief['window_end']).astimezone(UAE)
    c.text('أغريغيت | موجز القيادة الجيوسياسي والأمني',(1830,20,1730,72),52,True,INK)
    c.text('قراءة معمقة لمشهد إقليمي متغير',(2250,88,1320,46),28,True,NAVY2)
    _globe(c,3668,58,34,NAVY)
    date_ar=f"{AR_WEEKDAYS[end.weekday()]} {end.day} {AR_MONTHS[end.month]} {end.year} | {end.strftime('%H:%M')} بتوقيت الإمارات"
    c.text(date_ar,(150,26,1350,46),28,True,INK,'left')
    c.text('معلومات موثقة قدر الإمكان.. لقرارات أكثر استنارة',(150,84,1350,38),22,False,MUTED,'left')
    c.text(title,(1350,116,1140,36),23,True,NAVY,'center')
    c.rule(55,154,W-110,BORDER,2)


def _panel(c,box,title,color=NAVY,header_h=92):
    x,y,w,h=map(int,box)
    c.shadow((x,y,w,h),offset=7,radius=24)
    c.rounded((x,y,w,h),fill=PAPER,outline=BORDER,radius=24,width=2)
    c.d.rounded_rectangle((x,y,x+w,y+header_h),radius=24,fill=color)
    c.d.rectangle((x,y+header_h-24,x+w,y+header_h),fill=color)
    c.text(title,(x+28,y+17,w-56,58),36,True,'white')
    return x+28,y+header_h+20,w-56,h-header_h-38

def _circle_number(c,cx,cy,n,color):
    c.d.ellipse((cx-30,cy-30,cx+30,cy+30),fill=color)
    c.text(str(n),(cx-30,cy-22,60,44),24,True,'white','center')

def _mini_event(c,event,index,box):
    x,y,w,h=map(int,box)
    _,color=SEVERITY.get(event.get('severity','low'),('منخفض',MUTED))
    c.rounded((x,y,w,h),fill='#FAFCFD',outline='#DFE8EE',radius=17,width=1)
    _circle_number(c,x+w-42,y+43,index,color)
    c.text(event.get('title_ar',''),(x+22,y+16,w-92,68),27,True,color)
    c.text(event.get('summary_ar',''),(x+22,y+92,w-44,h-108),22,False,INK)

def is_uae(event):
    text=(event.get('title_ar','')+' '+event.get('summary_ar',''))
    return event.get('region')=='gcc' and (
        any(s.get('country')=='AE' for s in event.get('sources',[])) or
        any(k in text for k in ('الإمارات','الامارات','أبوظبي','ابوظبي','دبي','الشارقة'))
    )

def _stats_values(brief):
    events=brief.get('events',[])
    health=brief.get('health',[])
    active=sum(r.get('status') in ('active','social_only') for r in health)
    return [
        ('أحداث',len(events),GOLD),
        ('أولويات مرتفعة',sum(e.get('severity')=='high' for e in events),RED),
        ('مناطق مغطاة',f'{len({e.get("region") for e in events if e.get("region")})}/{len(REGIONS)}',GREEN),
        ('أخبار الإمارات',sum(is_uae(e) for e in events),BLUE),
        ('مصادر مستجيبة',active,NAVY),
        ('تقارير مدخلة',brief.get('input_count',0),BLUE),
        ('رصد اجتماعي',sum(any(s.get('kind')=='social' for s in e.get('sources',[])) for e in events),TEAL),
        ('الفترة','6 ساعات',TEAL),
    ]

def stats(c,brief):
    vals=list(reversed(_stats_values(brief)))
    margin=55; gap=10
    card_w=(W-2*margin-gap*7)//8
    y=168; h=128
    for i,(label,value,color) in enumerate(vals):
        x=margin+i*(card_w+gap)
        c.rounded((x,y,card_w,h),fill=PAPER,outline='#D8E1E7',radius=14,width=2)
        c.d.line((x+86,y+18,x+86,y+h-18),fill='#E3E9ED',width=2)
        c.d.ellipse((x+23,y+35,x+63,y+75),outline=color,width=5)
        c.text(label,(x+102,y+16,card_w-118,38),22,True,NAVY)
        c.text(str(value),(x+102,y+58,card_w-118,54),34,True,INK)


def _event_by_region(events):
    out={}
    for e in events:
        if e.get('region') not in out:
            out[e.get('region')]=e
    return out

REGION_SHAPES={
    'north_africa':[(45,145),(105,110),(250,118),(330,138),(420,150),(460,205),(420,265),(310,275),(205,255),(115,245),(55,205)],
    'sahel':[(115,255),(310,275),(420,265),(475,320),(430,388),(300,404),(180,382),(100,330)],
    'sudan':[(460,272),(555,278),(590,350),(548,422),(460,405),(430,338)],
    'horn':[(565,330),(642,342),(690,410),(646,452),(592,420),(548,390)],
    'somalia':[(650,388),(724,405),(770,462),(724,490),(670,452),(635,420)],
    'gcc':[(650,205),(760,210),(812,260),(770,320),(680,310),(635,258)],
    'yemen':[(680,310),(770,320),(752,370),(685,382),(640,345)],
    'iraq':[(596,158),(662,152),(694,206),(650,228),(598,210)],
    'iran':[(700,130),(820,142),(850,210),(810,266),(742,250),(694,206)],
    'turkey':[(535,75),(675,75),(714,120),(650,152),(556,144),(505,112)],
    'levant':[(548,145),(585,148),(600,198),(570,216),(545,188)],
    'palestine_israel':[(558,198),(574,198),(578,231),(560,238),(551,219)],
    'jordan':[(580,198),(610,202),(623,240),(592,250),(575,228)],
    'pakistan':[(850,165),(922,178),(950,238),(920,290),(858,274),(810,235)],
    'afghanistan':[(842,104),(916,112),(943,160),(922,192),(858,178),(820,145)],
}
REGION_LABELS={
    'north_africa':(250,190),'sahel':(270,330),'sudan':(510,338),'horn':(620,390),'somalia':(710,446),
    'gcc':(720,260),'yemen':(710,346),'iraq':(635,187),'iran':(770,190),'turkey':(610,108),
    'levant':(565,167),'palestine_israel':(546,224),'jordan':(612,226),'pakistan':(885,225),'afghanistan':(883,142)
}
MAP_NAMES={
    'north_africa':'شمال أفريقيا','sahel':'الساحل الأفريقي','sudan':'السودان','horn':'القرن الأفريقي',
    'somalia':'الصومال','gcc':'الخليج','yemen':'اليمن','iraq':'العراق','iran':'إيران','turkey':'تركيا',
    'levant':'لبنان / سوريا','palestine_israel':'فلسطين / إسرائيل','jordan':'الأردن','pakistan':'باكستان','afghanistan':'أفغانستان'
}

def _severity_fill(event):
    if not event:
        return '#BFD7E8'
    sev=event.get('severity')
    if sev=='high': return '#F18A94'
    if sev=='medium': return '#F3C967'
    if sev=='low': return '#8FD3A7'
    return '#BFD7E8'

def vector_map(c,box,events):
    x,y,w,h=map(int,box)
    c.rounded((x,y,w,h),fill='#DFF1F9',outline='#B6D0DD',radius=22,width=2)
    c.text('خريطة نطاق التغطية',(x+20,y+12,w-40,38),21,True,NAVY)
    first=_event_by_region(events)
    sx=(w-70)/1000.0
    sy=(h-65)/520.0
    oy=y+50
    for region,pts in REGION_SHAPES.items():
        mapped=[(x+35+px*sx,oy+py*sy) for px,py in pts]
        c.d.polygon(mapped,fill=_severity_fill(first.get(region)),outline='#FFFFFF')
        c.d.line(mapped+[mapped[0]],fill='#E7EDF1',width=2)
    for region,(lx,ly) in REGION_LABELS.items():
        label=MAP_NAMES[region]
        size=17 if region in ('palestine_israel','levant') else 19
        c.text(label,(x+35+(lx-72)*sx,oy+(ly-16)*sy,144*sx,34*sy),size,True,INK,'center',1.25)
    legend=[('توتر مرتفع','#F18A94'),('توتر متوسط','#F3C967'),('وضع مستقر نسبياً','#8FD3A7'),('مراقبة / لا تحديث','#BFD7E8')]
    lx=x+40; ly=y+h-112
    for i,(label,color) in enumerate(legend):
        yy=ly+i*25
        c.d.ellipse((lx,yy,lx+16,yy+16),fill=color,outline='#FFFFFF')
        c.text(label,(lx+26,yy-4,240,25),15,True,INK,'left',1.2)
    c.text('الصومال مدرج كنطاق مستقل ضمن التغطية',(x+w-610,y+h-44,575,28),16,True,NAVY)

def _changes(brief,limit=4):
    current=brief.get('events',[])
    previous=brief.get('previous_events') or []
    if not previous:
        if brief.get('sample'):
            return [
                'إضافة الصومال كنطاق مستقل في خريطة التغطية.',
                'زيادة إبراز مؤشرات البحر الأحمر والقرن الأفريقي.',
                'توسيع الرصد الاجتماعي مع فصل الادعاءات عن الأخبار المؤكدة.',
                'إبراز التغيرات الجوهرية فقط مقارنة بالإحاطة السابقة.',
            ]
        return ['لا توجد إحاطة سابقة محفوظة للمقارنة في هذه الدورة.']
    prev_titles={re.sub(r'\s+',' ',p.get('title_ar','')).strip() for p in previous}
    changes=[]
    for e in current:
        title=re.sub(r'\s+',' ',e.get('title_ar','')).strip()
        if title and title not in prev_titles:
            changes.append('جديد: '+title)
        if len(changes)>=limit: break
    if not changes:
        changes.append('لا تغيرات جوهرية جديدة في العناوين الرئيسية مقارنة بالإحاطة السابقة.')
    return changes

def _world_context(events,limit=4):
    preferred=[e for e in events if e.get('topic') in ('diplomacy','sanctions','strategic_infrastructure')]
    pool=preferred+[e for e in events if e not in preferred]
    out=[]
    for e in pool:
        t=e.get('title_ar','')
        if t and t not in out:
            out.append(t)
        if len(out)>=limit: break
    return out

def _numbered_lines(c,items,box,size=24,color=INK,limit=4):
    x,y,w,h=map(int,box)
    items=[i for i in items if i][:limit]
    if not items:
        c.text('لا توجد عناصر إضافية مؤهلة في هذه النافذة.',(x,y,w,h),size,False,MUTED)
        return
    step=max(58,h//max(1,len(items)))
    palette=[GREEN,BLUE,GOLD,PURPLE]
    for i,item in enumerate(items):
        cy=y+i*step+28
        _circle_number(c,x+w-34,cy,i+1,palette[i%len(palette)])
        c.text(item,(x,y+i*step,w-82,step-8),size,i==0,color)

def _analysis_summary(events):
    if not events:
        return 'لا تتوفر مواد مؤهلة كافية لإصدار خلاصة تحليلية في هذه النافذة.'
    lead=events[0]
    assessment=lead.get('assessment_ar') or 'لا يتوفر تقدير مدعوم بالأدلة.'
    covered=len({e.get('region') for e in events if e.get('region')})
    high=sum(e.get('severity')=='high' for e in events)
    return f'{assessment} تغطي هذه الدورة {covered} منطقة وبها {high} تطورات مصنفة أولوية مرتفعة. استمرار الرصد مطلوب مع الحفاظ على الفصل بين الوقائع والتقدير.'

TOPIC_AR={
    'diplomacy':'الدبلوماسية والاتصالات',
    'military':'التحركات العسكرية',
    'security':'الأمن والاستقرار',
    'political_stability':'الاستقرار السياسي',
    'humanitarian_conflict':'الأوضاع الإنسانية',
    'sanctions':'العقوبات والقيود',
    'strategic_infrastructure':'البنية التحتية الاستراتيجية',
}

def _topic_distribution(events,limit=5):
    counts={}
    for e in events:
        key=e.get('topic') or 'security'
        counts[key]=counts.get(key,0)+1
    # If editorial classification is too concentrated, use region coverage as a
    # deterministic secondary breakdown rather than leaving most of the panel empty.
    if len(counts)<limit:
        for e in events:
            key='region:'+str(e.get('region') or '')
            if key!='region:':
                counts[key]=counts.get(key,0)+1
    total=max(1,sum(counts.values()))
    ranked=sorted(counts.items(),key=lambda kv:(-kv[1],kv[0]))[:limit]
    out=[]
    for k,v in ranked:
        label=REGIONS.get(k[7:],k) if k.startswith('region:') else TOPIC_AR.get(k,k)
        out.append((label,v,round(v*100/total)))
    return out

def _detail_row(c,event,index,box):
    x,y,w,h=map(int,box)
    color=SEVERITY.get(event.get('severity','low'),('منخفض',MUTED))[1]
    c.d.rectangle((x+w-8,y+8,x+w,y+h-8),fill=color)
    c.d.line((x,y+h,x+w,y+h),fill='#E2E8EC',width=2)
    c.rounded((x+w-72,y+18,52,52),fill=PALE_BLUE,outline=None,radius=10,width=1)
    c.text(str(index),(x+w-72,y+27,52,32),20,True,NAVY,'center')
    tile_x=x+w-300
    c.rounded((tile_x,y+12,190,h-24),fill='#EEF3F6',outline='#DCE5EA',radius=12,width=1)
    c.text(REGIONS.get(event.get('region'),'إقليمي'),(tile_x+10,y+34,170,58),22,True,color,'center')
    c.text(event.get('title_ar',''),(x+8,y+12,w-330,68),27,True,NAVY)
    c.text(event.get('summary_ar',''),(x+8,y+84,w-330,h-94),20,False,INK)

def _alerts_panel(c,box,events):
    x,y,w,h=_panel(c,box,'مؤشرات الإنذار والمتابعة',GREEN)
    items=sorted(events,key=lambda e:({'high':0,'medium':1,'low':2}.get(e.get('severity'),3)))[:4]
    if not items:
        c.text('لا توجد مؤشرات إنذار مؤهلة في هذه النافذة.',(x,y,w,120),22,True,MUTED); return
    step=max(108,h//len(items))
    for i,e in enumerate(items):
        sev,color=SEVERITY.get(e.get('severity','low'),('منخفض',GREEN))
        c.text(sev,(x+w-150,y+i*step+10,130,34),19,True,color,'center')
        c.text(e.get('title_ar',''),(x+8,y+i*step+6,w-175,62),23,True,INK)
        c.text(e.get('watch_ar',''),(x+8,y+i*step+72,w-30,step-80),18,False,MUTED)
        c.rule(x,y+(i+1)*step-4,w,BORDER,1)

def _assess_panel(c,box,events):
    x,y,w,h=_panel(c,box,'التقديرات التحليلية',PURPLE)
    vals=_assessments(events,3)
    if not vals:
        c.text('لا تتوفر تقديرات تحليلية مدعومة في هذه النافذة.',(x,y,w,110),22,True,MUTED); return
    step=max(98,h//len(vals))
    for i,item in enumerate(vals):
        c.rounded((x+w-52,y+i*step+8,40,40),fill='#EEE8F7',outline=None,radius=9,width=1)
        c.text(str(i+1),(x+w-52,y+i*step+15,40,24),16,True,PURPLE,'center')
        c.text(item,(x+8,y+i*step,w-74,step-8),20,False,INK)

def _regional_implications(events,limit=4):
    out=[]
    for e in events:
        a=e.get('assessment_ar')
        if a and a not in out: out.append(a)
        if len(out)>=limit: break
    return out

def _discussion_panel(c,box,brief):
    x,y,w,h=_panel(c,box,'الرصد الاجتماعي واتجاهات الخطاب',BLUE)
    events=brief.get('events',[])
    c.text('أبرز موضوعات النقاش خلال نافذة الست ساعات',(x,y,w,44),26,True,NAVY)
    yy=y+52
    for i,(name,count,pct) in enumerate(_topic_distribution(events,5)):
        cy=yy+i*66
        c.rounded((x+w-50,cy,40,40),fill=PALE_BLUE,outline=None,radius=10,width=1)
        c.text(str(i+1),(x+w-50,cy+7,40,24),16,True,NAVY,'center')
        c.text(name,(x+8,cy+2,w-185,34),21,True,INK)
        base_w=w-220; bar_w=max(12,int(base_w*pct/100))
        c.d.rounded_rectangle((x+8,cy+42,x+8+base_w,cy+52),radius=5,fill='#E7EDF1')
        c.d.rounded_rectangle((x+8,cy+42,x+8+bar_w,cy+52),radius=5,fill=[RED,GOLD,BLUE,GREEN,PURPLE][i%5])
        c.text(f'{pct}%',(x+w-140,cy+8,76,26),16,True,INK,'center')
    divider=yy+5*66+8
    c.rule(x,divider,w,BORDER,2)
    c.text('حالة الإسناد في المواد المنشورة',(x,divider+14,w,38),25,True,NAVY)
    social=sum(any(s.get('kind')=='social' for s in e.get('sources',[])) for e in events)
    attributed=sum(e.get('status_ar')=='تقرير منسوب' for e in events)
    high=sum(e.get('severity')=='high' for e in events)
    cards=[('رصد اجتماعي',social,TEAL),('تقارير منسوبة',attributed,BLUE),('أولوية مرتفعة',high,RED)]
    cw=(w-24)//3
    for i,(label,val,color) in enumerate(cards):
        xx=x+i*(cw+12)
        c.rounded((xx,divider+60,cw,120),fill='#F8FBFC',outline='#E0E8ED',radius=12,width=1)
        c.text(str(val),(xx+8,divider+74,cw-16,40),27,True,color,'center')
        c.text(label,(xx+8,divider+112,cw-16,34),18,True,INK,'center')
    ny=divider+205
    c.text('أبرز الروايات المتداولة',(x,ny,w,38),25,True,NAVY)
    social_items=_social_items(events,4)
    narratives=social_items or [e.get('title_ar','') for e in events[:4]]
    for i,item in enumerate(narratives[:4]):
        c.text('• '+item,(x+8,ny+42+i*58,w-16,50),19,False,INK)
    caution_y=y+h-142
    c.rounded((x,caution_y,w,128),fill=PALE_RED,outline='#F1C9CE',radius=12,width=1)
    c.text('معلومة متداولة تتطلب الحذر',(x+18,caution_y+10,w-36,34),21,True,RED)
    caution=(social_items[0] if social_items else 'لا توجد حالياً إشارة اجتماعية منفردة تستدعي التحذير؛ يستمر الرصد مع الفصل بين الادعاء والخبر.')
    c.text(caution,(x+18,caution_y+50,w-36,64),17,False,INK)

def _global_indicators(c,box,brief):
    x,y,w,h=_panel(c,box,'مؤشرات عالمية ذات صلة',PURPLE)
    events=brief.get('events',[])
    vals=[
        ('أمن الملاحة',sum(any(k in (e.get('title_ar','')+' '+e.get('summary_ar','')) for k in ('البحر الأحمر','الملاحة','ميناء','خليج عدن')) for e in events),BLUE),
        ('تصعيد مرتفع',sum(e.get('severity')=='high' for e in events),RED),
        ('مسارات دبلوماسية',sum(e.get('topic')=='diplomacy' for e in events),GREEN),
        ('نطاقات محدثة',len({e.get('region') for e in events if e.get('region')}),GOLD),
    ]
    step=max(48,h//4)
    for i,(label,val,color) in enumerate(vals):
        yy=y+i*step
        c.text(label,(x+8,yy,w-165,34),19,True,INK)
        c.text(str(val),(x+w-150,yy,72,34),22,True,color,'center')
        c.text('↑' if val else '→',(x+w-66,yy,46,30),18,True,color,'center')

def _uae_panel(c,box,events):
    x,y,w,h=_panel(c,box,'أخبار الإمارات',NAVY)
    uae=[e for e in events if is_uae(e)][:3]
    if not uae:
        c.text('لا يوجد تحديث إماراتي مؤهل خلال نافذة الست ساعات الحالية.',(x,y,w,130),23,True,MUTED)
        return
    step=max(150,h//len(uae))
    for i,e in enumerate(uae):
        yy=y+i*step
        _circle_number(c,x+w-34,yy+32,i+1,[GREEN,BLUE,GOLD][i%3])
        c.text(e.get('title_ar',''),(x,yy,w-82,58),24,True,NAVY)
        c.text(e.get('summary_ar',''),(x,yy+62,w-18,step-76),18,False,INK)
        if i<len(uae)-1: c.rule(x,yy+step-8,w,BORDER,1)

def _maritime_event(events):
    keys=('البحر الأحمر','خليج عدن','الملاحة','ممرات بحرية','سفن','ميناء','الموانئ','بحر العرب','هرمز')
    for e in events:
        text=(e.get('title_ar','')+' '+e.get('summary_ar',''))
        if any(k in text for k in keys):
            return e
    return None

def _maritime_panel(c,box,events):
    x,y,w,h=_panel(c,box,'تحديثات الملاحة في الشرق الأوسط',NAVY)
    e=_maritime_event(events)
    if not e:
        c.text('لا يوجد تحديث بحري مؤهل في النافذة الحالية؛ يستمر رصد البحر الأحمر وخليج عدن وبحر العرب ومضيق هرمز.',
               (x,y,w,h),22,True,MUTED)
        return
    sev,color=SEVERITY.get(e.get('severity','low'),('منخفض',GREEN))
    c.rounded((x+w-145,y,120,38),fill=PALE_RED if e.get('severity')=='high' else PALE_GOLD,outline=None,radius=10,width=1)
    c.text(sev,(x+w-145,y+5,120,26),17,True,color,'center')
    c.text(e.get('title_ar',''),(x,y,w-170,74),25,True,NAVY)
    c.text(e.get('summary_ar',''),(x,y+82,w,h-160),19,False,INK)
    c.text('للمتابعة: '+(e.get('watch_ar') or 'متابعة التحديثات الموثقة للممرات البحرية.'),
           (x,y+h-66,w,54),18,True,TEAL)

def _trend_metrics(events):
    return [
        ('أحداث مرتفعة',sum(e.get('severity')=='high' for e in events),RED),
        ('أحداث متوسطة',sum(e.get('severity')=='medium' for e in events),GOLD),
        ('مسارات دبلوماسية',sum(e.get('topic')=='diplomacy' for e in events),GREEN),
        ('إشارات اجتماعية',sum(any(s.get('kind')=='social' for s in e.get('sources',[])) for e in events),TEAL),
        ('نطاقات محدثة',len({e.get('region') for e in events if e.get('region')}),BLUE),
        ('تحديثات بحرية',sum(any(k in (e.get('title_ar','')+' '+e.get('summary_ar','')) for k in ('البحر الأحمر','خليج عدن','الملاحة','هرمز','بحر العرب')) for e in events),NAVY),
    ]

def _metric_grid(c,box,events):
    x,y,w,h=_panel(c,box,'المؤشرات التحليلية',BLUE)
    vals=_trend_metrics(events)
    gap=18; cols=2; rows=3
    cw=(w-gap)//2; ch=(h-gap*2)//3
    for i,(label,val,color) in enumerate(vals):
        row=i//2; col=i%2
        xx=x+col*(cw+gap); yy=y+row*(ch+gap)
        c.rounded((xx,yy,cw,ch),fill='#F8FAFB',outline='#E0E6EB',radius=14,width=1)
        c.text(str(val),(xx+18,yy+20,110,ch-40),34,True,color,'center')
        c.text(label,(xx+142,yy+18,cw-162,ch-36),20,True,INK)

def page1(brief,path):
    c=Canvas()
    masthead(c,brief,1,'المشهد العام')
    stats(c,brief)
    events=brief.get('events',[])

    _uae_panel(c,(55,330,980,720),events)
    _discussion_panel(c,(55,1080,980,940),brief)

    cx,cy,cw,ch=_panel(c,(1070,330,1650,1340),'التحليل التفصيلي لأبرز التطورات',RED)
    rows=[e for e in events if not is_uae(e)][:6]
    if rows:
        rh=ch//6
        for i,e in enumerate(rows):
            _detail_row(c,e,i+1,(cx,cy+i*rh,cw,rh))
    else:
        c.text('لا توجد تطورات مؤهلة خلال نافذة التغطية.',(cx,cy,cw,150),26,True,MUTED)

    bx,by,bw,bh=_panel(c,(1070,1700,805,320),'التغيرات منذ الإحاطة السابقة',GOLD)
    _numbered_lines(c,_changes(brief,4),(bx,by,bw,bh),17,INK,4)
    bx,by,bw,bh=_panel(c,(1905,1700,815,320),'انعكاسات محتملة على المصالح الإقليمية',TEAL)
    _numbered_lines(c,_regional_implications(events,4),(bx,by,bw,bh),17,INK,4)

    _alerts_panel(c,(2755,330,1030,690),events)
    _assess_panel(c,(2755,1050,1030,520),events)
    _global_indicators(c,(2755,1600,1030,420),brief)

    c.text('المعلومات منسوبة إلى مصادرها | التحليل الآلي ليس تحققاً مستقلاً',(1010,2096,1820,28),18,False,MUTED,'center')
    c.text('الصفحة 1 من 3',(58,2090,280,34),18,True,MUTED,'left')
    c.save(path)
    return c.truncated


def _region_card(c,region,event,index,box):
    x,y,w,h=map(int,box)
    color=SEVERITY.get((event or {}).get('severity','low'),('منخفض',MUTED))[1] if event else '#8BA4B4'
    c.rounded((x,y,w,h),fill=PAPER,outline='#D9E2E8',radius=12,width=2)
    c.d.rectangle((x,y,x+w,y+48),fill=color)
    c.text(REGIONS[region],(x+18,y+7,w-36,32),20,True,'white')
    if not event:
        c.text('لا يوجد تحديث مؤهل خلال النافذة الحالية.',(x+18,y+70,w-36,h-86),18,False,MUTED)
        return
    c.text(event.get('title_ar',''),(x+18,y+64,w-36,54),20,True,INK)
    c.text(event.get('summary_ar',''),(x+18,y+120,w-36,h-150),16,False,INK)
    c.text(f'[{index}] {event.get("status_ar","")}',(x+18,y+h-28,w-36,20),13,True,color)


def page2(brief,path):
    c=Canvas()
    masthead(c,brief,2,'المشهد الإقليمي التفصيلي')
    stats(c,brief)
    events=brief.get('events',[])
    first=_event_by_region(events)
    indexes={}
    for i,e in enumerate(events,1):
        indexes.setdefault(e.get('region'),i)
    regions=list(REGIONS)
    cols=3; rows=6
    left=55; top=330; gap_x=22; gap_y=18
    card_w=(W-110-gap_x*(cols-1))//cols
    card_h=(1705-gap_y*(rows-1))//rows
    for n,region in enumerate(regions):
        col=n%cols; row=n//cols
        x=left+col*(card_w+gap_x)
        y=top+row*(card_h+gap_y)
        _region_card(c,region,first.get(region),indexes.get(region,0),(x,y,card_w,card_h))
    c.text(f'{len(REGIONS)} نطاقاً مستقلاً — مصر وعُمان والصومال تظهر كنطاقات مستقلة في التغطية.',
           (840,2055,2160,34),18,True,NAVY,'center')
    c.text('الصفحة 2 من 3',(58,2090,280,34),18,True,MUTED,'left')
    c.save(path)
    return c.truncated


def _social_items(events,limit=6):
    out=[]
    for e in events:
        social=[s for s in e.get('sources',[]) if s.get('kind')=='social']
        if social:
            names=' / '.join(s.get('source','') for s in social[:2])
            out.append(f'{names}: {e.get("summary_ar","")}')
        if len(out)>=limit: break
    return out

def _assessments(events,limit=6):
    out=[]
    for e in events:
        a=e.get('assessment_ar')
        if a: out.append(a)
        if len(out)>=limit: break
    return out

def _watch_items(events,limit=6):
    out=[]
    for e in events:
        w=e.get('watch_ar')
        if w: out.append(w)
        if len(out)>=limit: break
    return out

def page3(brief,path):
    c=Canvas()
    masthead(c,brief,3,'التحليل والمؤشرات')
    stats(c,brief)
    events=brief.get('events',[])

    _metric_grid(c,(55,330,1120,760),events)

    x,y,w,h=_panel(c,(55,1120,1120,900),'اتجاهات الخطاب والرصد المفتوح',TEAL)
    topics=_topic_distribution(events,5)
    yy=y
    for i,(name,count,pct) in enumerate(topics):
        row_h=118
        cy=yy+i*row_h
        c.text(name,(x,cy,w-190,38),22,True,INK)
        c.rounded((x+w-150,cy,120,40),fill=PALE_BLUE,outline=None,radius=10,width=1)
        c.text(f'{pct}%',(x+w-150,cy+6,120,28),20,True,NAVY,'center')
        c.d.rounded_rectangle((x,cy+54,x+w-32,cy+68),radius=7,fill='#E4EAEE')
        bar=max(16,int((w-32)*pct/100))
        c.d.rounded_rectangle((x,cy+54,x+bar,cy+68),radius=7,fill=[RED,GOLD,BLUE,GREEN,TEAL][i%5])
    c.text('النسب مؤشر توزيع داخل مواد هذه الدورة وليست استطلاعاً للرأي العام.',
           (x,y+h-46,w,34),16,False,MUTED)

    x,y,w,h=_panel(c,(1210,330,1450,830),'التقديرات والتحولات',PURPLE)
    c.text(_analysis_summary(events),(x,y,w,170),27,True,INK)
    c.rule(x,y+188,w,BORDER,2)
    _numbered_lines(c,_assessments(events,5),(x,y+220,w,h-240),21,INK,5)

    _maritime_panel(c,(1210,1190,1450,830),events)

    x,y,w,h=_panel(c,(2695,330,1090,790),'مؤشرات الإنذار المبكر',GREEN)
    _numbered_lines(c,_watch_items(events,6),(x,y,w,h),20,INK,6)

    x,y,w,h=_panel(c,(2695,1150,1090,870),'ما تغير منذ الإحاطة السابقة',GOLD)
    _numbered_lines(c,_changes(brief,6),(x,y,w,h),20,INK,6)

    c.text('المعلومات منسوبة إلى مصادرها | التحليل الآلي ليس تحققاً مستقلاً',(1010,2096,1820,28),18,False,MUTED,'center')
    c.text('الصفحة 3 من 3',(58,2090,280,34),18,True,MUTED,'left')
    c.save(path)
    return c.truncated


def render(brief,output):
    output=Path(output)
    output.mkdir(parents=True,exist_ok=True)
    paths=[output/'arabic-p1.png',output/'arabic-p2.png',output/'arabic-p3.png']
    truncations=page1(brief,paths[0])+page2(brief,paths[1])+page3(brief,paths[2])
    return paths,truncations

def references(brief,path):
    lines=[
        'النشرة الجيوسياسية والأمنية — أغريغيت',
        'الفترة: '+brief['window_start']+' — '+brief['window_end'],
        'الملخصات منسوبة إلى المصادر؛ مراجعة النموذج ليست تحققاً مستقلاً.',
        ''
    ]
    if brief.get('sample'):
        lines.insert(0,'نموذج اصطناعي — ليس أخباراً حقيقية')
    for i,e in enumerate(brief.get('events',[]),1):
        lines.extend([
            f'[{i}] '+e.get('title_ar',''),
            e.get('summary_ar',''),
            'تقدير تحليلي: '+e.get('assessment_ar',''),
            'للمتابعة: '+e.get('watch_ar',''),
            e.get('status_ar','')
        ])
        for s in e.get('sources',[]):
            date=datetime.fromtimestamp(s['published'],UAE).strftime('%Y-%m-%d %H:%M')
            lines.extend([s.get('source','')+' | '+date+' بتوقيت الإمارات',s.get('url','')])
        lines.append('')
    lines+=['حالة الجمع:']+[
        r.get('name','')+' — '+({'active':'مستجيب','social_only':'اجتماعي فقط','failed':'تعذر الجمع'}.get(r.get('status'),'غير متاح'))
        for r in brief.get('health',[])
    ]
    Path(path).write_text('\n'.join(lines),encoding='utf-8')
