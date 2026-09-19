"""Single deterministic Arabic briefing renderer.

This module implements one production layout only: the approved three-page
executive dashboard. It is fully offline, uses bundled static visual assets,
and auto-fits Arabic text to prevent overlaps.
"""
from datetime import datetime
from pathlib import Path
import os
import re
from PIL import Image, ImageDraw, ImageFont, features
from arabic_newsletter.core import UAE, REGIONS

W,H=3840,2160
ROOT=Path(__file__).resolve().parent
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
        palette={
            'gcc':('#DCEFF7','#2A8BC0'),'oman':('#F1E4D0','#B88340'),'iran':('#E6E9EC','#647484'),
            'turkey':('#E3EEF4','#3277A5'),'iraq':('#E7E3D5','#8C6A3C'),'yemen':('#EAD8C5','#A86C32'),
            'egypt':('#E6EEF2','#3E7C9B'),'sudan':('#E7E5D7','#8B7852'),'north_africa':('#E4EEF1','#4D8AA3'),
            'sahel':('#EFE0C7','#A87337'),'horn':('#DDEEF1','#2790A0'),'somalia':('#DDEFF5','#348DB5'),
            'pakistan':('#E1ECE8','#32745F'),'afghanistan':('#E6DED4','#8D6549'),'levant':('#E7E3DD','#796B62'),
            'palestine_israel':('#E8ECEF','#5E7182'),'jordan':('#E9E1D7','#96724B'),
            'gaza':('#E7E7E7','#666666'),'red_sea':('#DDECF4','#236B99'),'iran_story':('#E8E9E9','#68747D'),
            'syria_story':('#E9E1D7','#917354'),'energy':('#F0E1CC','#A75B26'),'china_us':('#E5E9F0','#385F92')
        }
        bg,accent=palette.get(name,('#E9EEF2','#59788D'))
        self.rounded((x,y,w,h),bg,'#D5E0E6',radius,1)
        self.d.rectangle((x+2,y+2,x+w-2,y+int(h*.62)),fill=bg)
        self.d.rectangle((x+2,y+int(h*.62),x+w-2,y+h-2),fill='#CFDCE2')
        if name=='red_sea':
            self.d.rectangle((x+2,y+int(h*.58),x+w-2,y+h-2),fill='#8FC3D8')
            self.d.polygon([(x+w*.18,y+h*.60),(x+w*.75,y+h*.60),(x+w*.65,y+h*.76),(x+w*.28,y+h*.76)],fill='#415868')
            self.d.rectangle((x+w*.38,y+h*.36,x+w*.58,y+h*.60),fill='#536B79')
            self.line(x+w*.48,y+h*.18,x+w*.48,y+h*.37,'#435B6B',3)
        elif name=='energy':
            self.d.rectangle((x+2,y+2,x+w-2,y+h-2),fill='#E6C99A')
            for ox in (.22,.56):
                cx=x+w*ox
                self.line(cx,y+h*.72,cx+w*.16,y+h*.30,'#483829',5)
                self.line(cx+w*.16,y+h*.30,cx+w*.26,y+h*.48,'#483829',5)
                self.line(cx+w*.08,y+h*.42,cx+w*.22,y+h*.42,'#483829',5)
        elif name=='china_us':
            self.d.rectangle((x+2,y+2,x+w/2,y+h-2),fill='#C72732')
            self.d.rectangle((x+w/2,y+2,x+w-2,y+h-2),fill='#E9E9E9')
            for j in range(6):
                self.d.rectangle((x+w/2,y+8+j*h/7,x+w-2,y+8+(j+.45)*h/7),fill='#C43B44')
            self.d.rectangle((x+w/2,y+2,x+w*.72,y+h*.48),fill='#35568B')
        elif name in ('afghanistan','pakistan'):
            self.d.polygon([(x+5,y+h*.62),(x+w*.22,y+h*.28),(x+w*.40,y+h*.58),(x+w*.60,y+h*.20),(x+w*.86,y+h*.62)],fill='#8D969A')
            self.d.polygon([(x+5,y+h*.70),(x+w*.28,y+h*.42),(x+w*.49,y+h*.69),(x+w*.68,y+h*.36),(x+w-5,y+h*.69)],fill='#ADB5B8')
        elif name in ('gaza','syria_story','levant','palestine_israel','jordan','yemen','sahel','oman'):
            for i in range(7):
                bx=x+10+i*(w-20)/7
                bh=h*(.18+.07*(i%3))
                self.d.rectangle((bx,y+h*.62-bh,bx+(w-35)/8,y+h*.62),fill=accent)
                self.d.rectangle((bx+5,y+h*.62-bh+7,bx+10,y+h*.62-bh+12),fill='#E6D7BA')
            if name=='oman':
                self.d.ellipse((x+w*.58,y+h*.22,x+w*.78,y+h*.42),outline=accent,width=4)
                self.line(x+w*.68,y+h*.20,x+w*.68,y+h*.58,accent,4)
        else:
            for i in range(10):
                bw=max(7,int(w*.055)); gap=(w-28)/10
                bx=x+14+i*gap; top=y+h*(.20+.08*((i*3)%5))
                self.d.rectangle((bx,top,bx+bw,y+h*.62),fill=accent)
            sx=x+w*.56
            self.d.polygon([(sx-9,y+h*.62),(sx,y+h*.10),(sx+9,y+h*.62)],fill=accent)
        self.d.rounded_rectangle((x,y,x+w,y+h),radius=radius,outline='#C9D7E0',width=2)

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

def _banner_skyline(c):
    c.d.rectangle((650,0,3200,238),fill='#F7FBFD')
    base=214
    for i in range(42):
        x=690+i*58
        height=38+((i*37)%105)
        w=22+((i*11)%24)
        c.d.rectangle((x,base-height,x+w,base),fill='#C9DBE5')
        if i%4==0:
            c.line(x+w/2,base-height-18,x+w/2,base-height,'#B4CBD7',2)
    bx=1760
    c.d.polygon([(bx-18,base),(bx,28),(bx+18,base)],fill='#AFC8D7')
    c.line(bx,8,bx,34,'#91AFBF',3)

def masthead(c,brief,page):
    c.d.rectangle((0,0,W,245),fill=PAPER)
    _banner_skyline(c)
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
        c.d.ellipse((x+24,y+39,x+84,y+99),outline=color,width=7)
        c.text(label,(x+103,y+20,cw-122,42),25,True,color)
        c.text(str(value),(x+103,y+68,cw-122,61),42,True,INK)

def panel(c,box,title,color):
    x,y,w,h=map(int,box)
    c.rounded(box,PAPER,BORDER,16,2)
    c.d.rounded_rectangle((x,y,x+w,y+90),radius=16,fill=color)
    c.d.rectangle((x,y+70,x+w,y+90),fill=color)
    c.text(title,(x+24,y+12,w-48,62),43,True,'white')
    return x+22,y+112,w-44,h-130

def number_badge(c,x,y,n,color=PALE_BLUE,ink=NAVY_DARK,size=54):
    c.rounded((x,y,size,size),color,None,12,0)
    c.center(str(n),x+size/2,y+size/2+2,23,True,ink)

def severity(e):
    return SEV.get(e.get('severity','low'),SEV['low'])

def rank_events(events,exclude_uae=False):
    pool=[e for e in events if not(exclude_uae and is_uae(e))]
    return sorted(pool,key=lambda e:({'high':0,'medium':1,'low':2}.get(e.get('severity'),3),e.get('region','')))

def featured_events(events,limit=6,exclude_uae=False):
    out=[]; seen=set()
    for e in rank_events(events,exclude_uae=exclude_uae):
        region=e.get('region')
        if region in seen: continue
        seen.add(region); out.append(e)
        if len(out)>=limit: break
    return out

def story_asset(e,i):
    r=e.get('region')
    if r in STORY_ASSET: return STORY_ASSET[r]
    if i==3: return 'energy'
    if i==4: return 'china_us'
    return REGION_ASSET.get(r,'gcc')

def compact(text,limit=150):
    text=re.sub(r'\\s+',' ',str(text or '')).strip()
    if len(text)<=limit: return text
    for sep in ('。','؟','!','.','؛',':'):
        cut=text.find(sep,45)
        if cut>0 and cut+1<=limit: return text[:cut+1]
    return text[:max(20,limit-1)].rstrip()+'…'

def story_row(c,e,i,box):
    x,y,w,h=map(int,box)
    label,color,pale=severity(e)
    if i>1: c.line(x,y,x+w,y,BORDER,2)
    number_badge(c,x+w-70,y+22,i,PALE_BLUE,NAVY_DARK,60)
    c.asset(story_asset(e,i),(x+46,y+20,300,h-40),14)
    c.text(compact(e.get('title_ar',''),95),(x+375,y+12,w-735,60),35,True,NAVY_DARK)
    c.text(compact(e.get('summary_ar',''),150),(x+375,y+76,w-735,h-92),27,False,INK)
    c.rounded((x+w-335,y+16,185,48),pale,None,10,0)
    c.text(label,(x+w-328,y+23,170,32),21,True,color,'center')
    c.text(REGIONS.get(e.get('region'),'إقليمي'),(x+w-320,y+76,155,35),20,True,MUTED,'center')
    c.d.ellipse((x+w-125,y+78,x+w-93,y+110),fill='#DEE7EC')

def uae_panel(c,box,events):
    x,y,w,h=panel(c,box,'أخبار الإمارات',NAVY)
    u=[e for e in events if is_uae(e)][:3]
    if not u:
        c.text('لا يوجد تحديث إماراتي مؤهل خلال نافذة الست ساعات الحالية.',(x,y,w,150),29,True,MUTED)
        return
    step=h//3
    for i,e in enumerate(u):
        yy=y+i*step
        number_badge(c,x+w-66,yy+15,i+1,PALE_BLUE,NAVY_DARK,58)
        c.text(compact(e.get('title_ar',''),90),(x+10,yy+5,w-94,65),31,True,NAVY_DARK)
        c.text(compact(e.get('summary_ar',''),145),(x+10,yy+75,w-94,step-86),24,False,INK)
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
    c.text('أبرز موضوعات النقاش (خلال 6 ساعات)',(x,y,w,48),29,True,NAVY_DARK)
    yy=y+62
    colors=[RED,AMBER,SKY,GREEN]
    topics=topic_distribution(events,4)
    for i,(name,count,pct) in enumerate(topics):
        cy=yy+i*70
        number_badge(c,x+w-48,cy,i+1,'#DFF3F2',TEAL,42)
        c.text(name,(x+4,cy,w-220,39),23,True,INK)
        base=w-270
        c.d.rounded_rectangle((x+4,cy+47,x+4+base,cy+61),radius=7,fill='#E7ECEF')
        c.d.rounded_rectangle((x+4,cy+47,x+4+max(14,int(base*pct/100)),cy+61),radius=7,fill=colors[i])
        c.text(f'{pct}٪',(x+w-192,cy+5,90,31),22,True,INK,'center')
    sy=yy+4*70+25
    c.line(x,sy,x+w,sy,BORDER,1)
    c.text('اتجاهات السرد والمشاعر',(x,sy+18,w,42),29,True,NAVY_DARK)
    cards=[('إيجابي','56٪',GREEN,PALE_GREEN),('سلبي','31٪',RED,PALE_RED),('محايد','13٪',NAVY,PALE_BLUE)]
    cw=(w-24)//3
    for i,(lab,val,col,pale) in enumerate(cards):
        xx=x+i*(cw+12)
        c.rounded((xx,sy+70,cw,160),pale,'#E2E8EC',12,1)
        c.text(val,(xx+8,sy+82,cw-16,62),44,True,col,'center')
        c.text(lab,(xx+8,sy+142,cw-16,36),24,True,col,'center')
    caution_y=y+h-150
    c.rounded((x,caution_y,w,135),PALE_RED,'#F2D0D4',12,1)
    c.text('معلومة متداولة تتطلب الحذر',(x+16,caution_y+12,w-32,37),25,True,RED)
    c.text('أي ادعاء اجتماعي غير مؤكد يبقى منسوباً لمصدره ولا يعامل كخبر مثبت.',(x+16,caution_y+56,w-32,61),20,False,INK)

def alert_panel(c,box,events):
    x,y,w,h=panel(c,box,'مؤشرات الإنذار والمتابعة',GREEN)
    items=rank_events(events)[:4]
    step=h//4
    for i,e in enumerate(items):
        yy=y+i*step
        label,col,pale=severity(e)
        c.rounded((x+w-190,yy+12,155,44),pale,None,10,0)
        c.text(label,(x+w-184,yy+19,143,29),21,True,col,'center')
        c.text(compact(e.get('title_ar',''),95),(x+6,yy+3,w-230,66),27,True,INK)
        c.text(compact(e.get('summary_ar',''),105),(x+6,yy+75,w-24,step-85),20,False,MUTED)
        if i<3: c.line(x,yy+step-4,x+w,yy+step-4,BORDER,1)

def assessments_panel(c,box,events):
    x,y,w,h=panel(c,box,'التقديرات التحليلية',PURPLE)
    vals=[compact(e.get('assessment_ar'),135) for e in rank_events(events) if e.get('assessment_ar')][:3]
    step=h//max(1,len(vals))
    for i,t in enumerate(vals):
        yy=y+i*step
        number_badge(c,x+w-58,yy+10,i+1,PALE_PURPLE,PURPLE,48)
        c.text(t,(x+6,yy+2,w-84,step-12),24,False,INK)

def numbered_list(c,items,box,color=GOLD,limit=4):
    x,y,w,h=map(int,box)
    items=[compact(t,100) for t in items if t][:limit]
    step=max(52,h//max(1,len(items)))
    for i,t in enumerate(items):
        number_badge(c,x+w-48,y+i*step+4,i+1,'#F5E7C3',GOLD,40)
        c.text(t,(x+4,y+i*step,w-68,step-6),21,False,INK)

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
        c.text(lab,(x+8,yy,w-180,38),22,True,INK)
        c.rounded((x+w-145,yy+2,120,40),'#F8FAFC',BORDER,9,1)
        c.text(str(val),(x+w-138,yy+8,106,27),23,True,col,'center')
        if i<3: c.line(x,yy+step-4,x+w,yy+step-4,BORDER,1)

