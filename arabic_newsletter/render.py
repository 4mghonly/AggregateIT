"""Three-slide Arabic commander-style briefing with dense RTL-safe layout."""
from collections import Counter
from datetime import datetime
from pathlib import Path
import os
from PIL import Image, ImageDraw, ImageFont, features
from .core import UAE, REGIONS

W,H=3840,2160
PAPER,WHITE,INK,MUTED,BORDER='#F5F7F8','#FFFFFF','#10233D','#66768A','#D6E0E8'
RED,BLUE,GOLD,GREEN='#C4252D','#0E527F','#9A6B12','#117A53'
BLUE2,PALE_BLUE,PALE_GREEN,PALE_GOLD,PALE_RED='#0B6AA8','#EAF4FA','#EDF8F3','#FBF5E9','#FFF0F1'
SEVERITY={'high':('مرتفع',RED),'medium':('متوسط',GOLD),'low':('منخفض',GREEN)}

class Canvas:
    def __init__(self):
        if not features.check_feature('raqm'): raise RuntimeError('Pillow RAQM required for correct Arabic shaping')
        self.image=Image.new('RGB',(W,H),PAPER); self.d=ImageDraw.Draw(self.image); self.boxes=[]; self.truncated=0
    def font(self,size,bold=False):
        candidates=[
            '/usr/share/fonts/truetype/noto/NotoKufiArabic-Bold.ttf' if bold else '/usr/share/fonts/truetype/noto/NotoKufiArabic-Regular.ttf',
            '/usr/share/fonts/truetype/noto/NotoSansArabic-Bold.ttf' if bold else '/usr/share/fonts/truetype/noto/NotoSansArabic-Regular.ttf',
        ]
        root=Path(os.getenv('ARABIC_FONT_DIR','/usr/share/fonts/truetype/dejavu'))
        candidates.append(str(root/('DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf')))
        for path in candidates:
            if Path(path).exists():
                return ImageFont.truetype(path,size,layout_engine=ImageFont.Layout.RAQM)
        raise RuntimeError('No Arabic-capable font found')
    def width(self,text,font): return self.d.textlength(text,font=font,direction='rtl',language='ar')
    def lines(self,text,width,font):
        lines=[]; line=''
        for word in str(text or '').split():
            if line and self.width(line+' '+word,font)>width: lines.append(line); line=''
            while self.width(word,font)>width:
                n=len(word)-1
                while n>1 and self.width(word[:n],font)>width: n-=1
                if line: lines.append(line); line=''
                lines.append(word[:n]); word=word[n:]
            line=(line+' '+word).strip()
        if line: lines.append(line)
        return lines
    def text(self,text,box,size=34,bold=False,color=INK,align='right'):
        x,y,w,h=map(int,box); font=self.font(size,bold); step=round(size*1.48)
        lines=self.lines(text,w,font); capacity=max(0,h//step)
        if len(lines)>capacity:
            self.truncated+=1; lines=lines[:capacity]
            if lines:
                while lines[-1] and self.width(lines[-1]+'…',font)>w: lines[-1]=lines[-1][:-1]
                lines[-1]=lines[-1].rstrip()+'…'
        for i,line in enumerate(lines):
            bounds=self.d.textbbox((0,0),line,font=font,direction='rtl',language='ar'); tw=bounds[2]-bounds[0]
            xx=x+(w-tw if align=='right' else (w-tw)/2 if align=='center' else 0); yy=y+i*step
            self.d.text((xx-bounds[0],yy-bounds[1]),line,font=font,fill=color,direction='rtl',language='ar')
            self.boxes.append((xx,yy,xx+tw,yy+bounds[3]-bounds[1],x,y,x+w,y+h))
        return y+len(lines)*step
    def rule(self,x,y,w,color=BORDER): self.d.line((x,y,x+w,y),fill=color,width=3)
    def panel(self,box,title=None,color=BLUE):
        x,y,w,h=map(int,box)
        self.d.rounded_rectangle((x,y,x+w,y+h),radius=18,fill=WHITE,outline=BORDER,width=2)
        if title:
            header_h=82
            self.d.rounded_rectangle((x,y,x+w,y+header_h),radius=18,fill=color)
            self.d.rectangle((x,y+header_h-18,x+w,y+header_h),fill=color)
            self.text(title,(x+28,y+13,w-56,54),34,True,WHITE)
            return x+24,y+header_h+18,w-48,h-header_h-34
        return x+24,y+20,w-48,h-40
    def save(self,path):
        for left,top,right,bottom,x,y,x2,y2 in self.boxes:
            if left<x-1 or top<y-1 or right>x2+1 or bottom>y2+1: raise RuntimeError('Text exceeded its measured box')
        self.image.save(path,optimize=True)

def _draw_flag(c,x,y):
    w,h,red=118,72,28
    c.d.rectangle((x,y,x+w,y+h),fill=WHITE,outline=BORDER,width=1)
    c.d.rectangle((x,y,x+red,y+h),fill='#D71920')
    stripe=h/3
    c.d.rectangle((x+red,y,x+w,y+stripe),fill='#00732F')
    c.d.rectangle((x+red,y+stripe,x+w,y+2*stripe),fill=WHITE)
    c.d.rectangle((x+red,y+2*stripe,x+w,y+h),fill='#000000')

def _draw_skyline(c):
    c.d.rectangle((0,0,W,190),fill='#F6FAFC')
    c.d.rectangle((0,124,W,190),fill='#EDF4F8')
    for i,x in enumerate(range(40,W-40,54)):
        hh=25+((i*37)%75); ww=20+((i*11)%24)
        c.d.rectangle((x,157-hh,x+ww,157),fill='#B9CEDA')
        if i%7==0:
            c.d.line((x+ww//2,157-hh-26,x+ww//2,157-hh),fill='#A8C2D0',width=3)
    bx=1640
    c.d.rectangle((bx,34,bx+18,157),fill='#8EADBE')
    c.d.rectangle((bx-11,76,bx+29,157),fill='#9FB9C7')
    c.d.rectangle((bx-25,110,bx+43,157),fill='#ACC2CE')
    c.d.line((bx+9,5,bx+9,34),fill='#779CAE',width=4)

def masthead(c,brief,page,title):
    end=datetime.fromisoformat(brief['window_end']).astimezone(UAE)
    _draw_skyline(c); _draw_flag(c,90,44)
    c.text('أغريغيت — موجز المشهد الجيوسياسي والأمني',(1770,22,1530,68),42,True,INK)
    c.text('قراءة معمقة لمشهد إقليمي متغير',(2050,86,1250,44),27,True,BLUE)
    c.text('رؤية أوسع',(3320,20,430,30),18,True,MUTED)
    c.text('فهم أعمق',(3320,52,430,30),18,True,MUTED)
    c.text('قرار أكثر استقراراً',(3320,84,430,30),18,True,MUTED)
    c.text(end.strftime('%H:%M')+' بتوقيت الإمارات  •  '+end.strftime('%Y-%m-%d'),(485,36,1120,44),24,True,INK,'left')
    c.text('معلومات موجزة، قرارات أكثر استنارة',(485,86,1040,40),21,False,MUTED,'left')
    c.text(title,(1680,160,1900,44),24,True,BLUE)
    c.text(f'الصفحة {page} من 3',(70,2100,440,38),22,True,MUTED,'left')
    c.text('المعلومات منسوبة إلى مصادرها  |  التحليل الآلي ليس تحققاً مستقلاً',(1300,2100,2350,38),21,False,MUTED,'center')

def refs(event,index):
    names=' / '.join(s['source'] for s in event['sources'])
    return f'[{index}] {event["status_ar"]} | {names}'

def is_uae(event):
    text=(event.get('title_ar','')+' '+event.get('summary_ar',''))
    return event.get('region')=='gcc' and (any(s.get('country')=='AE' for s in event.get('sources',[])) or any(k in text for k in ('الإمارات','الامارات','أبوظبي','ابوظبي','دبي','الشارقة')))

def _mini_card(c,event,index,box,accent=BLUE):
    x,y,w,h=map(int,box)
    _,sev,_=SEVERITY.get(event.get('severity'),SEVERITY['low'])
    pale=PALE_RED if event.get('severity')=='high' else PALE_GOLD if event.get('severity')=='medium' else PALE_GREEN
    c.d.rounded_rectangle((x,y,x+w,y+h),radius=14,fill=pale,outline=BORDER,width=1)
    c.d.ellipse((x+w-58,y+20,x+w-20,y+58),fill=sev)
    c.text(str(index),(x+w-56,y+22,34,28),18,True,WHITE,'center')
    c.text(event.get('title_ar',''),(x+22,y+14,w-98,66),27,True,accent)
    c.text(event.get('summary_ar',''),(x+22,y+86,w-44,h-104),22,False,INK)

def _severity_color(events,region):
    matches=[e for e in events if e.get('region')==region]
    if any(e.get('severity')=='high' for e in matches): return RED
    if any(e.get('severity')=='medium' for e in matches): return '#F0B94B'
    if matches: return '#7DC58B'
    return '#B9D4E4'

def draw_scope_map(c,box,events):
    x,y,w,h=map(int,box)
    c.d.rounded_rectangle((x,y,x+w,y+h),radius=16,fill='#E9F4FA',outline='#B9D5E4',width=2)
    c.text('البحر المتوسط',(x+500,y+28,430,38),18,True,BLUE2,'center')
    c.text('الخليج',(x+1110,y+216,220,34),18,True,BLUE2,'center')
    c.text('البحر الأحمر',(x+840,y+350,250,38),17,True,BLUE2,'center')
    c.text('المحيط الهندي',(x+1190,y+430,350,36),17,True,BLUE2,'center')
    shapes={
      'north_africa':[(80,150),(310,105),(520,130),(590,240),(450,330),(170,315)],
      'sahel':[(155,322),(480,330),(610,410),(485,510),(200,485),(95,405)],
      'sudan':[(585,350),(760,348),(800,505),(610,545),(535,445)],
      'levant':[(820,165),(885,155),(905,300),(842,315),(806,248)],
      'palestine_israel':[(878,212),(908,210),(916,302),(884,311)],
      'jordan':[(910,240),(975,236),(990,315),(930,325)],
      'iraq':[(990,202),(1110,195),(1165,300),(1030,332),(980,285)],
      'gcc':[(1100,320),(1360,315),(1435,425),(1270,475),(1090,410)],
      'iran':[(1160,170),(1400,160),(1495,300),(1390,355),(1185,310)],
      'turkey':[(820,78),(1100,65),(1140,145),(930,166),(800,132)],
      'yemen':[(1120,455),(1320,445),(1380,535),(1200,560),(1085,510)],
      'horn':[(785,530),(980,520),(1060,650),(880,690),(745,625)],
      'somalia':[(1010,560),(1145,605),(1105,745),(1000,690),(950,610)],
      'pakistan':[(1485,260),(1625,255),(1680,385),(1555,420),(1460,350)],
      'afghanistan':[(1430,145),(1585,130),(1635,245),(1490,270),(1405,220)],
    }
    sx=w/1750.0; sy=h/780.0
    for region,pts in shapes.items():
        poly=[(x+int(px*sx),y+int(py*sy)) for px,py in pts]
        c.d.polygon(poly,fill=_severity_color(events,region),outline=WHITE)
        cx=sum(p[0] for p in poly)/len(poly); cy=sum(p[1] for p in poly)/len(poly)
        size=13 if region in ('palestine_israel','levant','jordan') else 16
        c.text(REGIONS.get(region,region),(cx-100,cy-14,200,30),size,True,INK,'center')
    legend=[('توتر مرتفع',RED),('توتر متوسط','#F0B94B'),('تحديث منخفض','#7DC58B'),('مراقبة','#B9D4E4')]
    lx=x+24; ly=y+h-108
    for n,(label,col) in enumerate(legend):
        yy=ly+n*24
        c.d.ellipse((lx,yy+5,lx+13,yy+18),fill=col)
        c.text(label,(lx+20,yy,180,23),13,True,INK,'left')

def _change_lines(brief):
    current=brief.get('events',[])
    previous=brief.get('previous_events') or []
    if not previous: return [e.get('title_ar','') for e in current[:4]]
    old={str(e.get('title_ar','')).strip() for e in previous}
    fresh=[e.get('title_ar','') for e in current if str(e.get('title_ar','')).strip() not in old]
    return (fresh or [e.get('title_ar','') for e in current[:4]])[:4]

def _numbered(c,items,box,size=22,limit=4):
    x,y,w,h=map(int,box); vals=[str(v or '').strip() for v in items if str(v or '').strip()][:limit]
    if not vals:
        c.text('لا توجد تحديثات مؤهلة في هذه النافذة.',(x,y,w,h),size,False,MUTED); return
    step=max(58,h//max(1,limit)); colors=[GREEN,BLUE2,GOLD,'#6F2DA8']
    for row,value in enumerate(vals):
        cy=y+row*step+20; col=colors[row%len(colors)]
        c.d.ellipse((x+w-42,cy-18,x+w-4,cy+20),fill=col)
        c.text(str(row+1),(x+w-40,cy-15,34,28),18,True,WHITE,'center')
        c.text(value,(x,y+row*step,w-58,step-4),size,row==0,INK)

def event_card(c,event,index,box,analysis=False,compact=False):
    x,y,w,h=box; severity,color=SEVERITY[event['severity']]
    c.d.rectangle((x+w-8,y,x+w,y+h-8),fill=color); w-=24
    header_h=40 if compact else 46
    title_h=68 if compact else 104
    ref_h=31 if compact else 42
    gap=6
    c.text(REGIONS[event['region']]+' | '+severity+' | '+event['status_ar'],(x,y,w,header_h),24 if compact else 28,True,color)
    title_y=y+header_h+gap
    c.text(event['title_ar'],(x,title_y,w,title_h),28 if compact else 37,True)
    body_y=title_y+title_h+gap
    ref_y=y+h-ref_h
    available=max(30,ref_y-body_y-gap)
    if compact:
        body_size=23 if h<240 else 25
        if analysis:
            summary_h=max(42,int(available*0.42))
            assess_h=max(35,int(available*0.29))
            watch_h=max(35,available-summary_h-assess_h-2*gap)
            c.text(event['summary_ar'],(x,body_y,w,summary_h),body_size)
            ay=body_y+summary_h+gap
            c.text('التقدير: '+(event.get('assessment_ar') or 'لا يتوفر تقدير مدعوم.'),(x,ay,w,assess_h),22,False,BLUE)
            wy=ay+assess_h+gap
            c.text('للمتابعة: '+(event.get('watch_ar') or 'انتظار تحديث موثق.'),(x,wy,w,watch_h),21,False,GREEN)
        else:
            c.text(event['summary_ar'],(x,body_y,w,available),body_size)
    else:
        summary_h=min(170,max(70,int(available*0.48 if analysis else available)))
        c.text(event['summary_ar'],(x,body_y,w,summary_h),31)
        if analysis:
            ay=body_y+summary_h+gap
            remain=max(60,ref_y-ay-gap)
            assess_h=max(30,(remain-gap)//2)
            watch_h=max(30,remain-assess_h-gap)
            c.text('التقدير: '+(event.get('assessment_ar') or 'لا يتوفر تقدير مدعوم.'),(x,ay,w,assess_h),27,False,BLUE)
            c.text('للمتابعة: '+(event.get('watch_ar') or 'انتظار تحديث موثق.'),(x,ay+assess_h+gap,w,watch_h),26,False,GREEN)
    c.text(refs(event,index),(x,ref_y,w,ref_h),20 if compact else 25,False,MUTED)

def stats(c,brief):
    events=brief.get('events',[]); health=brief.get('health',[])
    active=sum(r.get('status') in ('active','social_only') for r in health)
    updated=len({e.get('region') for e in events if e.get('region') in REGIONS})
    vals=[
      ('أحداث',len(events),GOLD,PALE_GOLD),
      ('أولويات مرتفعة',sum(e.get('severity')=='high' for e in events),RED,PALE_RED),
      ('مناطق مغطاة',f'{updated} من {len(REGIONS)}',GREEN,PALE_GREEN),
      ('أخبار الإمارات',sum(is_uae(e) for e in events),BLUE2,PALE_BLUE),
      ('مصادر مستجيبة',active,BLUE2,PALE_BLUE),
      ('تقارير مدخلة',brief.get('input_count',0),BLUE2,PALE_BLUE),
      ('رصد اجتماعي',sum(any(s.get('kind')=='social' for s in e.get('sources',[])) for e in events),BLUE2,PALE_BLUE),
      ('الفترة','6 ساعات',GREEN,PALE_GREEN),
    ]
    left=55; gap=18; total=W-110; cw=(total-gap*7)/8; y=224; h=160
    for i,(label,value,color,pale) in enumerate(vals):
        x=left+(7-i)*(cw+gap)
        c.d.rounded_rectangle((x,y,x+cw,y+h),radius=18,fill=pale,outline=BORDER,width=2)
        c.d.ellipse((x+26,y+48,x+88,y+110),outline=color,width=6)
        c.text(label,(x+105,y+28,cw-125,40),23,True,MUTED)
        c.text(str(value),(x+100,y+78,cw-120,52),32,True,color)

def numbered_lines(c,items,box,size=29,color=INK,limit=5):
    x,y,w,h=box; step=max(62,int(h/max(1,limit)))
    for row,text in enumerate(items[:limit]): c.text('• '+text,(x,y+row*step,w,step-6),size,row==0,color)

def page1(brief,path):
    c=Canvas(); masthead(c,brief,1,'الملخص التنفيذي والتطورات ذات الأولوية'); stats(c,brief)
    events=brief.get('events',[])
    left_x,center_x,right_x=55,970,2940
    main_y,main_h=420,1110
    left_w,center_w,right_w=855,1910,845

    # أخبار الإمارات
    x,y,w,h=c.panel((left_x,main_y,left_w,main_h),'أخبار الإمارات',BLUE)
    uae=[(i,e) for i,e in enumerate(events,1) if is_uae(e)][:3]
    if uae:
        ch=(h-30)/3
        for row,(idx,e) in enumerate(uae):
            _mini_card(c,e,idx,(x,y+row*(ch+10),w,ch),BLUE2)
    else:
        c.text('لا يوجد تحديث إماراتي مؤهل في نافذة الست ساعات الحالية.',(x,y+80,w,180),28,True,MUTED)

    # التطور الرئيسي + خريطة النطاق (أصغر قليلاً من النموذج السابق)
    x,y,w,h=c.panel((center_x,main_y,center_w,main_h),'التطور الرئيسي',BLUE)
    if events:
        lead=events[0]
        c.text(lead.get('title_ar',''),(x+20,y,w-40,100),36,True,INK,'center')
        c.text(lead.get('summary_ar',''),(x+30,y+112,w-60,180),25,False,INK,'center')
        draw_scope_map(c,(x+100,y+310,w-200,550),events)
        c.text('مؤشر المتابعة: '+(lead.get('watch_ar') or 'انتظار تحديث موثق من المصادر.'),(x+30,y+h-110,w-60,70),22,True,GREEN)
    else:
        c.text('لا توجد مواد مستوفية لشروط النشر في النافذة المحددة.',(x,y+120,w,220),32,True,MUTED,'center')

    # أولويات المتابعة
    x,y,w,h=c.panel((right_x,main_y,right_w,main_h),'أولويات المتابعة',BLUE)
    high=[(i,e) for i,e in enumerate(events,1) if e.get('severity')=='high' and not is_uae(e)][:3]
    fallback=[(i,e) for i,e in enumerate(events,1) if not is_uae(e)]
    pri=list(high); used={i for i,_ in pri}
    for item in fallback:
        if item[0] not in used and len(pri)<3:
            pri.append(item); used.add(item[0])
    if pri:
        ch=(h-30)/3; accents=[RED,BLUE2,GOLD]
        for row,(idx,e) in enumerate(pri[:3]):
            _mini_card(c,e,idx,(x,y+row*(ch+10),w,ch),accents[row])
    else:
        c.text('لا توجد أولويات إضافية مؤهلة.',(x,y+80,w,180),28,True,MUTED)

    bottom_y,bottom_h=1560,500
    bx,by,bw,bh=c.panel((55,bottom_y,1290,bottom_h),'التغييرات منذ الإحاطة السابقة',GREEN)
    _numbered(c,_change_lines(brief),(bx,by,bw,bh),22,4)

    bx,by,bw,bh=c.panel((1385,bottom_y,1070,bottom_h),'سياق دولي',BLUE)
    context=[e.get('title_ar','') for e in events if e.get('region') not in ('gcc','palestine_israel','jordan')][:4]
    _numbered(c,context,(bx,by,bw,bh),21,4)

    bx,by,bw,bh=c.panel((2495,bottom_y,1290,bottom_h),'الخلاصة التحليلية',GOLD)
    assessment=(events[0].get('assessment_ar') if events else '') or 'لا تتوفر أدلة كافية لإصدار تقدير تحليلي موسع.'
    c.text(assessment,(bx+10,by+10,bw-20,220),25,True,INK)
    covered=len({e.get('region') for e in events if e.get('region') in REGIONS})
    c.d.rounded_rectangle((bx+60,by+258,bx+bw-60,by+362),radius=14,fill=PALE_GOLD,outline='#E7D4A6',width=1)
    c.text(f'تغطية شاملة لـ {covered} من {len(REGIONS)} منطقة جغرافية — تشمل الصومال ضمن نطاق مستقل.',(bx+90,by+278,bw-180,58),22,True,GOLD,'center')
    c.save(path); return c.truncated

def region_card(c,region,event,index,box):
    x,y,w,h=map(int,box)
    color=SEVERITY[event['severity']][1] if event else MUTED
    pale=PALE_RED if event and event.get('severity')=='high' else PALE_GOLD if event and event.get('severity')=='medium' else PALE_GREEN if event else '#F4F7F9'
    c.d.rounded_rectangle((x,y,x+w,y+h),radius=14,fill=pale,outline=BORDER,width=1)
    c.text(REGIONS[region],(x+20,y+12,w-40,38),24,True,color); c.rule(x+20,y+54,w-40,color)
    if not event:
        c.text('لا يوجد تحديث مؤهل خلال نافذة التغطية الحالية.',(x+20,y+72,w-40,h-90),23,False,MUTED); return
    title_y=y+68; title_h=58; ref_h=27; ref_y=y+h-ref_h-8
    c.text(event['title_ar'],(x+20,title_y,w-40,title_h),24,True,INK)
    summary_y=title_y+title_h+4; summary_h=max(38,ref_y-summary_y-5)
    c.text(event['summary_ar'],(x+20,summary_y,w-40,summary_h),18)
    c.text(f'[{index}] {SEVERITY[event["severity"]][0]} | {event["status_ar"]}',(x+20,ref_y,w-40,ref_h),17,True,color)

def page2(brief,path):
    c=Canvas(); masthead(c,brief,2,'الموقف الإقليمي — تغطية جميع مناطق المسؤولية'); events=brief['events']
    first={}
    indexes={}
    for i,e in enumerate(events,1):
        if e['region'] not in first: first[e['region']]=e; indexes[e['region']]=i
    regions=list(REGIONS); cols=2; card_w=1768; card_h=216; gap_x=74; gap_y=8; start_y=278
    for n,region in enumerate(regions):
        col=n%cols; row=n//cols; x=115+col*(card_w+gap_x); y=start_y+row*(card_h+gap_y)
        region_card(c,region,first.get(region),indexes.get(region,0),(x,y,card_w,card_h))
    c.save(path); return c.truncated

def page3(brief,path):
    c=Canvas(); masthead(c,brief,3,'التفاصيل الاستخباراتية ومؤشرات القرار'); events=brief['events']
    pi=[(i,e) for i,e in enumerate(events,1) if e['region']=='palestine_israel'][:3]
    jo=[(i,e) for i,e in enumerate(events,1) if e['region']=='jordan'][:2]
    social=[(i,e) for i,e in enumerate(events,1) if any(s['kind']=='social' for s in e['sources'])][:4]
    used={i for i,_ in pi+jo}; additional=[(i,e) for i,e in enumerate(events,1) if i not in used][:7]
    box=c.panel((115,280,1120,790),'فلسطين / إسرائيل',RED); x,y,w,h=box
    if pi:
        for row,(i,e) in enumerate(pi): event_card(c,e,i,(x,y+row*218,w,205),analysis=False,compact=True)
    else: c.text('لا يوجد تحديث مؤهل في هذه النافذة.',(x,y,w,160),32,False,MUTED)
    box=c.panel((115,1100,1120,900),'الأردن',GREEN); x,y,w,h=box
    if jo:
        for row,(i,e) in enumerate(jo): event_card(c,e,i,(x,y+row*370,w,350),analysis=True,compact=True)
    else: c.text('لا يوجد تحديث مؤهل في هذه النافذة.',(x,y,w,160),32,False,MUTED)
    box=c.panel((1285,280,1190,1720),'تفاصيل إضافية',GOLD); x,y,w,h=box
    for row,(i,e) in enumerate(additional): event_card(c,e,i,(x,y+row*224,w,210),analysis=False,compact=True)
    box=c.panel((2525,280,1200,510),'مؤشرات الإنذار والمتابعة',BLUE); x,y,w,h=box
    numbered_lines(c,[e.get('watch_ar') for e in events if e.get('watch_ar')],(x,y,w,h),27,BLUE,5)
    box=c.panel((2525,820,1200,510),'التقديرات التحليلية',RED); x,y,w,h=box
    numbered_lines(c,[e.get('assessment_ar') for e in events if e.get('assessment_ar')],(x,y,w,h),27,BLUE,5)
    box=c.panel((2525,1360,1200,640),'تصريحات ورصد اجتماعي',GREEN); x,y,w,h=box
    if social:
        numbered_lines(c,[f'[{i}] '+e['summary_ar'] for i,e in social],(x,y,w,h),26,INK,4)
    else: c.text('لا توجد مواد اجتماعية مؤهلة. الرصد الاجتماعي لا يُعامل كتأكيد مستقل.',(x,y,w,170),30,False,MUTED)
    c.save(path); return c.truncated

def render(brief,output):
    output=Path(output); output.mkdir(parents=True,exist_ok=True)
    paths=[output/'arabic-p1.png',output/'arabic-p2.png',output/'arabic-p3.png']
    truncations=page1(brief,paths[0])+page2(brief,paths[1])+page3(brief,paths[2])
    return paths,truncations

def references(brief,path):
    lines=['النشرة الجيوسياسية والأمنية — أغريغيت','الفترة: '+brief['window_start']+' — '+brief['window_end'],
      'الملخصات منسوبة إلى المصادر؛ مراجعة النموذج ليست تحققاً مستقلاً.','']
    if brief.get('sample'): lines.insert(0,'نموذج اصطناعي — ليس أخباراً حقيقية')
    for i,e in enumerate(brief['events'],1):
        lines.extend([f'[{i}] '+e['title_ar'],e['summary_ar'],'تقدير تحليلي: '+e['assessment_ar'],'للمتابعة: '+e['watch_ar'],e['status_ar']])
        for s in e['sources']:
            date=datetime.fromtimestamp(s['published'],UAE).strftime('%Y-%m-%d %H:%M')
            lines.extend([s['source']+' | '+date+' بتوقيت الإمارات',s['url']])
        lines.append('')
    lines+=['حالة الجمع:']+[r['name']+' — '+({'active':'مستجيب','social_only':'اجتماعي فقط','failed':'تعذر الجمع'}.get(r['status'],'غير متاح')) for r in brief['health']]
    Path(path).write_text('\n'.join(lines),encoding='utf-8')
