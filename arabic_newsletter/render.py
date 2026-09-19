"""Approved three-slide Arabic geopolitical briefing layout.

The first page follows the map-centred visual approved for Discord:
UAE news at left, a dominant central development panel with a compact vector map,
follow-up priorities at right, KPI cards above, and three analytical panels below.
All drawing is offline, RTL-shaped, measured, and bounded.
"""
from datetime import datetime
from pathlib import Path
import os
import re
from PIL import Image, ImageDraw, ImageFont, features
from .core import UAE, REGIONS

W,H=3840,2160
BG='#F4F8FA'
PAPER='#FFFFFF'
INK='#10243E'
MUTED='#5D6E7E'
BORDER='#CBD8E2'
NAVY='#0C4F78'
NAVY2='#123E63'
RED='#B31F2B'
BLUE='#1768A8'
GOLD='#9A6A12'
GREEN='#177653'
TEAL='#168A86'
PURPLE='#5F278D'
PALE_BLUE='#EAF4F8'
PALE_GOLD='#FBF3DD'
PALE_GREEN='#EAF6F1'
PALE_RED='#FBECEE'
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
    _skyline(c)
    _flag(c,60,44,1.0)
    end=datetime.fromisoformat(brief['window_end']).astimezone(UAE)
    c.text('أغريغيت | موجز المشهد الجيوسياسي والأمني',(1870,36,1760,72),50,True,NAVY)
    c.text('قراءة معمقة لمشهد إقليمي متغير',(2080,112,1520,50),31,True,NAVY2)
    _globe(c,3690,78,42,NAVY)
    c.text('رؤية أوسع لفهم أعمق لقرار أكثر استنارة',(3350,120,310,84),22,True,MUTED,'center')
    date_ar=f"{AR_WEEKDAYS[end.weekday()]} {end.day} {AR_MONTHS[end.month]} {end.year} | {end.strftime('%H:%M')} بتوقيت الإمارات"
    c.text(date_ar,(580,38,1160,48),25,True,INK,'left')
    c.text('معلومات موثقة قدر الإمكان.. وقراءة أكثر استنارة',(580,94,1160,40),23,False,MUTED,'left')
    c.text(title,(1260,178,1320,54),30,True,NAVY,'center')
    if brief.get('sample'):
        c.text('نموذج تصميم تجريبي — ليس أخباراً حقيقية',(1250,218,1340,32),19,True,RED,'center')

def _panel(c,box,title,color=NAVY,header_h=88):
    x,y,w,h=map(int,box)
    c.shadow((x,y,w,h),offset=7,radius=24)
    c.rounded((x,y,w,h),fill=PAPER,outline=BORDER,radius=24,width=2)
    c.d.rounded_rectangle((x,y,x+w,y+header_h),radius=24,fill=color)
    c.d.rectangle((x,y+header_h-24,x+w,y+header_h),fill=color)
    c.text(title,(x+28,y+18,w-56,52),31,True,'white')
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
    margin=55; gap=18
    w=(W-2*margin-gap*7)//8
    y=268; h=166
    for i,(label,value,color) in enumerate(vals):
        x=margin+i*(w+gap)
        c.shadow((x,y,w,h),offset=5,radius=20)
        c.rounded((x,y,w,h),fill=PAPER,outline='#D4E1E8',radius=20,width=2)
        c.d.rounded_rectangle((x+12,y+12,x+80,y+80),radius=22,fill='#EEF7F7')
        c.d.ellipse((x+31,y+31,x+61,y+61),outline=color,width=5)
        c.text(label,(x+92,y+20,w-112,44),24,True,color)
        c.text(str(value),(x+92,y+72,w-112,68),36,True,INK)

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

def page1(brief,path):
    c=Canvas()
    masthead(c,brief,1,'المشهد العام')
    stats(c,brief)
    events=brief.get('events',[])
    uae=[e for e in events if is_uae(e)][:3]
    priorities=sorted(events,key=lambda e:({'high':0,'medium':1,'low':2}.get(e.get('severity'),3)))[:3]

    left=_panel(c,(55,470,885,1100),'أخبار الإمارات',NAVY)
    lx,ly,lw,lh=left
    if uae:
        card_h=(lh-28*2)//3
        for i,e in enumerate(uae):
            _mini_event(c,e,i+1,(lx,ly+i*(card_h+28),lw,card_h))
    else:
        c.text('لا يوجد تحديث إماراتي مؤهل في نافذة الست ساعات الحالية.',(lx,ly,lw,180),30,True,MUTED)

    cx,cy,cw,ch=_panel(c,(975,470,1880,1100),'التطور الرئيسي',NAVY)
    if events:
        lead=events[0]
        c.text(lead.get('title_ar',''),(cx,cy,cw,110),37,True,INK)
        c.text(lead.get('summary_ar',''),(cx,cy+116,cw,205),27,False,INK)
        map_w=1540; map_h=515
        map_x=cx+(cw-map_w)//2
        vector_map(c,(map_x,cy+330,map_w,map_h),events)
        c.text('المصدر: '+(' / '.join(s.get('source','') for s in lead.get('sources',[])[:3]) or '—'),
               (cx,cy+866,cw,42),18,False,MUTED)
    else:
        c.text('لا توجد مواد مستوفية لشروط النشر في النافذة المحددة.',(cx,cy,cw,200),35,True,MUTED)

    rx,ry,rw,rh=_panel(c,(2890,470,895,1100),'أولويات المتابعة',NAVY)
    if priorities:
        card_h=(rh-28*2)//3
        for i,e in enumerate(priorities):
            _mini_event(c,e,i+1,(rx,ry+i*(card_h+28),rw,card_h))
    else:
        c.text('لا توجد أولويات إضافية في هذه النافذة.',(rx,ry,rw,180),30,True,MUTED)

    bx,by,bw,bh=_panel(c,(55,1605,1250,455),'التغيرات منذ الإحاطة السابقة',GREEN)
    _numbered_lines(c,_changes(brief),(bx,by,bw,bh),23,INK,4)

    bx,by,bw,bh=_panel(c,(1340,1605,1215,455),'سياق دولي',NAVY)
    _numbered_lines(c,_world_context(events),(bx,by,bw,bh),23,INK,4)

    bx,by,bw,bh=_panel(c,(2590,1605,1195,455),'الخلاصة التحليلية',GOLD)
    c.text(_analysis_summary(events),(bx,by,bw,bh-74),25,True,INK)
    c.rounded((bx,by+bh-65,bw,55),fill=PALE_GOLD,outline='#E6D09C',radius=14,width=1)
    c.text(f'تغطية شاملة لـ {len(REGIONS)} نطاقاً جغرافياً — من الخليج إلى شمال أفريقيا وآسيا والقرن الأفريقي والصومال.',
           (bx+18,by+bh-55,bw-36,38),18,True,GOLD,'center')

    c.text('المعلومات منسوبة إلى مصادرها | التحليل الآلي ليس تحققاً مستقلاً',(1030,2092,1790,34),18,False,MUTED,'center')
    c.text('الصفحة 1 من 3',(58,2090,280,34),18,True,MUTED,'left')
    c.save(path)
    return c.truncated

def _region_card(c,region,event,index,box):
    x,y,w,h=map(int,box)
    color=SEVERITY.get((event or {}).get('severity','low'),('منخفض',MUTED))[1] if event else '#8BA4B4'
    c.shadow((x,y,w,h),offset=5,radius=18)
    c.rounded((x,y,w,h),fill=PAPER,outline='#D7E2E9',radius=18,width=2)
    c.d.rounded_rectangle((x,y,x+w,y+58),radius=18,fill=color)
    c.d.rectangle((x,y+40,x+w,y+58),fill=color)
    c.text(REGIONS[region],(x+20,y+10,w-40,38),23,True,'white')
    if not event:
        c.text('لا يوجد تحديث مؤهل خلال نافذة التغطية الحالية.',(x+22,y+78,w-44,h-94),21,False,MUTED)
        return
    c.text(event.get('title_ar',''),(x+22,y+76,w-44,70),24,True,INK)
    c.text(event.get('summary_ar',''),(x+22,y+150,w-44,h-194),19,False,INK)
    c.text(f'[{index}] {event.get("status_ar","")}',(x+22,y+h-34,w-44,26),15,True,color)

def page2(brief,path):
    c=Canvas()
    masthead(c,brief,2,'المشهد الإقليمي التفصيلي')
    events=brief.get('events',[])
    first=_event_by_region(events)
    indexes={}
    for i,e in enumerate(events,1):
        indexes.setdefault(e.get('region'),i)
    regions=list(REGIONS)
    cols=3
    gap_x=28; gap_y=22
    left=55; top=300
    card_w=(W-110-gap_x*(cols-1))//cols
    rows=5
    card_h=(1745-gap_y*(rows-1))//rows
    for n,region in enumerate(regions):
        col=n%cols; row=n//cols
        x=left+col*(card_w+gap_x)
        y=top+row*(card_h+gap_y)
        _region_card(c,region,first.get(region),indexes.get(region,0),(x,y,card_w,card_h))
    c.text('15 نطاقاً جغرافياً مستقلاً — الصومال يظهر كنطاق مستقل عن القرن الأفريقي.',(900,2070,2040,38),20,True,NAVY,'center')
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
    masthead(c,brief,3,'الرصد والتحليل ومؤشرات المتابعة')
    events=brief.get('events',[])

    x,y,w,h=_panel(c,(55,300,1170,760),'التغيرات منذ الإحاطة السابقة',GREEN)
    _numbered_lines(c,_changes(brief,6),(x,y,w,h),23,INK,6)

    x,y,w,h=_panel(c,(55,1090,1170,945),'سياق دولي أوسع',NAVY)
    _numbered_lines(c,_world_context(events,7),(x,y,w,h),23,INK,7)

    x,y,w,h=_panel(c,(1260,300,1230,760),'الرصد الاجتماعي والمصادر المفتوحة',TEAL)
    social=_social_items(events,6)
    if social:
        _numbered_lines(c,social,(x,y,w,h),21,INK,6)
    else:
        c.text('لا توجد مواد اجتماعية مؤهلة في هذه النافذة. المواد الاجتماعية لا تُعامل كتأكيد مستقل.',
               (x,y,w,180),26,True,MUTED)
        c.rounded((x,y+215,w,115),fill=PALE_GREEN,outline='#C9E8DB',radius=16,width=1)
        c.text('منهج الرصد: إشارات اجتماعية → إسناد للمصدر → فصل الادعاء عن الخبر → مراجعة قبل الإدراج.',
               (x+22,y+238,w-44,70),20,True,GREEN,'center')

    x,y,w,h=_panel(c,(1260,1090,1230,945),'مؤشرات الإنذار والمتابعة',BLUE)
    _numbered_lines(c,_watch_items(events,7),(x,y,w,h),22,INK,7)

    x,y,w,h=_panel(c,(2525,300,1260,1735),'الخلاصة التحليلية',GOLD)
    c.text(_analysis_summary(events),(x,y,w,260),29,True,INK)
    c.rule(x,y+280,w,GOLD,3)
    c.text('تقديرات تحليلية',(x,y+310,w,46),25,True,GOLD)
    _numbered_lines(c,_assessments(events,6),(x,y+372,w,770),22,INK,6)
    c.rule(x,y+1165,w,BORDER,2)
    c.text('مؤشرات التغطية',(x,y+1195,w,44),24,True,NAVY)
    vals=_stats_values(brief)
    yy=y+1255
    for i,(label,value,color) in enumerate(vals[:6]):
        row=i//2; col=i%2
        xx=x+col*(w//2)
        c.rounded((xx,yy+row*126,w//2-18,104),fill='#F8FBFC',outline='#DDE7EC',radius=14,width=1)
        c.text(label,(xx+14,yy+row*126+12,w//2-46,34),18,True,color)
        c.text(str(value),(xx+14,yy+row*126+48,w//2-46,42),25,True,INK)
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
