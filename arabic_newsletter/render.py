"""Three-slide Arabic commander-style briefing with dense RTL-safe layout."""
from collections import Counter
from datetime import datetime
from pathlib import Path
import os
from PIL import Image, ImageDraw, ImageFont, features
from .core import UAE, REGIONS

W,H=3840,2160
PAPER,INK,MUTED,BORDER='#F6F1E7','#1C1B18','#514B43','#C8BDAA'
RED,BLUE,GOLD,GREEN='#7D2A2A','#1F3864','#705514','#285C38'
SEVERITY={'high':('مرتفع',RED),'medium':('متوسط',GOLD),'low':('منخفض',MUTED)}

class Canvas:
    def __init__(self):
        if not features.check_feature('raqm'): raise RuntimeError('Pillow RAQM required for correct Arabic shaping')
        self.image=Image.new('RGB',(W,H),PAPER); self.d=ImageDraw.Draw(self.image); self.boxes=[]; self.truncated=0
    def font(self,size,bold=False):
        root=Path(os.getenv('ARABIC_FONT_DIR','/usr/share/fonts/truetype/dejavu'))
        return ImageFont.truetype(str(root/('DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf')),size,layout_engine=ImageFont.Layout.RAQM)
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
    def panel(self,box,title=None,color=RED):
        x,y,w,h=box; self.d.rectangle((x,y,x+w,y+h),outline=BORDER,width=2)
        if title:
            self.text(title,(x+28,y+18,w-56,62),36,True,color); self.rule(x+28,y+82,w-56,color)
            return x+30,y+101,w-60,h-120
        return x+30,y+24,w-60,h-48
    def save(self,path):
        for left,top,right,bottom,x,y,x2,y2 in self.boxes:
            if left<x-1 or top<y-1 or right>x2+1 or bottom>y2+1: raise RuntimeError('Text exceeded its measured box')
        self.image.save(path,optimize=True)

def masthead(c,brief,page,title):
    end=datetime.fromisoformat(brief['window_end']).astimezone(UAE)
    c.text('أغريغيت | موجز القيادة الجيوسياسي والأمني',(2030,30,1695,62),34,True)
    c.text(end.strftime('%Y-%m-%d  %H:%M')+' بتوقيت الإمارات',(115,32,1780,58),29,False,MUTED,'left')
    c.text(title,(500,98,2840,64),34,True,RED,'center')
    c.rule(115,175,3610,INK)
    c.text('المعلومات منسوبة إلى مصادرها | التقدير الآلي ليس تحققاً مستقلاً',(650,2088,3075,56),28,False,MUTED)
    c.text(f'الصفحة {page} من 3',(115,2088,500,56),28,True,MUTED,'left')

def refs(event,index):
    names=' / '.join(s['source'] for s in event['sources'])
    return f'[{index}] {event["status_ar"]} | {names}'

def is_uae(event):
    text=(event.get('title_ar','')+' '+event.get('summary_ar',''))
    return event.get('region')=='gcc' and (any(s.get('country')=='AE' for s in event.get('sources',[])) or any(k in text for k in ('الإمارات','الامارات','أبوظبي','ابوظبي','دبي','الشارقة')))

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
    events=brief['events']; health=brief['health']; active=sum(r.get('status') in ('active','social_only') for r in health)
    vals=[('أحداث',len(events)),('أولوية مرتفعة',sum(e['severity']=='high' for e in events)),
      ('مناطق بتحديث',f'{len({e["region"] for e in events})}/{len(REGIONS)}'),('أخبار الإمارات',sum(is_uae(e) for e in events)),
      ('مصادر مستجيبة',active),('تقارير مدخلة',brief['input_count']),
      ('رصد اجتماعي',sum(any(s['kind']=='social' for s in e['sources']) for e in events)),('الفترة','6 ساعات')]
    width=3610/8
    for i,(label,value) in enumerate(vals):
        x=115+(7-i)*width
        if i<7: c.d.line((x,205,x,327),fill=BORDER,width=2)
        c.text(label,(x+8,198,width-16,48),27,True,MUTED,'center'); c.text(str(value),(x+8,254,width-16,68),40,True,INK,'center')
    c.rule(115,347,3610,INK)

def numbered_lines(c,items,box,size=29,color=INK,limit=5):
    x,y,w,h=box; step=max(62,int(h/max(1,limit)))
    for row,text in enumerate(items[:limit]): c.text('• '+text,(x,y+row*step,w,step-6),size,row==0,color)

def page1(brief,path):
    c=Canvas(); masthead(c,brief,1,'الموقف العام وأولويات القيادة'); stats(c,brief); events=brief['events']
    uae=[(i,e) for i,e in enumerate(events,1) if is_uae(e)][:3]
    high=[(i,e) for i,e in enumerate(events,1) if e['severity']=='high' and not is_uae(e)][:3]
    left=c.panel((115,385,1080,1045),'أخبار الإمارات',GREEN); x,y,w,h=left
    if uae:
        for row,(i,e) in enumerate(uae): event_card(c,e,i,(x,y+row*292,w,276),analysis=False,compact=True)
    else: c.text('لا يوجد تحديث إماراتي مؤهل في نافذة الست ساعات الحالية.',(x,y,w,180),34,True,MUTED)
    center=c.panel((1245,385,1430,1045),'التطور الرئيسي',RED); x,y,w,h=center
    if events:
        lead=events[0]; c.text(lead['title_ar'],(x,y,w,170),48,True)
        c.rule(x,y+178,w,GOLD); yy=c.text(lead['summary_ar'],(x,y+205,w,270),35)
        yy=c.text('التقدير: '+(lead.get('assessment_ar') or 'لا يتوفر تقدير مدعوم بالأدلة.'),(x,yy+18,w,170),31,False,BLUE)
        c.text('مؤشر المتابعة: '+(lead.get('watch_ar') or 'انتظار تحديث موثق من المصدر.'),(x,yy+195,w,160),31,False,GREEN)
        c.text(refs(lead,1),(x,y+h-60,w,52),26,False,MUTED)
    else: c.text('لا توجد مواد مستوفية لشروط النشر في النافذة المحددة.',(x,y,w,260),44,True)
    right=c.panel((2725,385,1000,1045),'أولوية العمليات',BLUE); x,y,w,h=right
    if high:
        for row,(i,e) in enumerate(high): event_card(c,e,i,(x,y+row*292,w,276),compact=True)
    else: c.text('لا توجد أحداث إضافية مصنفة أولوية مرتفعة.',(x,y,w,180),33,False,MUTED)
    panels=[((115,1480,1115,520),'مؤشرات المتابعة',GREEN),((1380,1480,1115,520),'تطورات سريعة',GOLD),((2645,1480,1080,520),'تقدير القيادة',RED)]
    for box,label,color in panels:
        px,py,pw,ph=c.panel(box,label,color)
        if label=='مؤشرات المتابعة':
            numbered_lines(c,[e.get('watch_ar') for e in events if e.get('watch_ar')],(px,py,pw,ph),28,GREEN,5)
        elif label=='تطورات سريعة':
            numbered_lines(c,[e['title_ar'] for e in events[4:10]],(px,py,pw,ph),28,INK,5)
        else:
            note=events[0].get('assessment_ar') if events else ''
            c.text(note or 'لا تتوفر أدلة كافية لإصدار تقدير.',(px,py,pw,170),31,True,BLUE)
            c.text(f'التغطية: {len({e["region"] for e in events})} من {len(REGIONS)} مناطق. الغياب يعني عدم وجود تحديث مؤهل، لا غياب الأحداث.',(px,py+195,pw,155),28,False,MUTED)
    c.save(path); return c.truncated

def region_card(c,region,event,index,box):
    x,y,w,h=box; c.d.rectangle((x,y,x+w,y+h),outline=BORDER,width=2)
    color=SEVERITY[event['severity']][1] if event else MUTED
    c.text(REGIONS[region],(x+20,y+12,w-40,38),25,True,color); c.rule(x+20,y+54,w-40,color)
    if not event:
        c.text('لا يوجد تحديث مؤهل خلال نافذة التغطية الحالية.',(x+20,y+72,w-40,h-90),25,False,MUTED); return
    title_y=y+68; title_h=58; ref_h=27; ref_y=y+h-ref_h-8
    c.text(event['title_ar'],(x+20,title_y,w-40,title_h),26,True)
    summary_y=title_y+title_h+4
    summary_h=max(38,ref_y-summary_y-5)
    c.text(event['summary_ar'],(x+20,summary_y,w-40,summary_h),20)
    c.text(f'[{index}] {SEVERITY[event["severity"]][0]} | {event["status_ar"]}',(x+20,ref_y,w-40,ref_h),18,True,color)

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
