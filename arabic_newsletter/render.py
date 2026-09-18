"""3840x2160 Gazette geometry, original palette, native RTL shaping and measured bounds."""
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
        self.image=Image.new('RGB',(W,H),PAPER); self.d=ImageDraw.Draw(self.image)
        self.boxes=[]; self.truncated=0
    def font(self,size,bold=False):
        root=Path(os.getenv('ARABIC_FONT_DIR','/usr/share/fonts/truetype/dejavu'))
        return ImageFont.truetype(str(root/('DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf')),size,
          layout_engine=ImageFont.Layout.RAQM)
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
        x,y,w,h=map(int,box); font=self.font(size,bold); step=round(size*1.52)
        lines=self.lines(text,w,font); capacity=max(0,h//step)
        if len(lines)>capacity:
            self.truncated+=1; lines=lines[:capacity]
            if lines:
                while lines[-1] and self.width(lines[-1]+'…',font)>w: lines[-1]=lines[-1][:-1]
                lines[-1]=lines[-1].rstrip()+'…'
        for i,line in enumerate(lines):
            # Anchor to actual ink bounds, including Arabic ascenders/descenders.
            bounds=self.d.textbbox((0,0),line,font=font,direction='rtl',language='ar')
            tw=bounds[2]-bounds[0]
            xx=x+(w-tw if align=='right' else (w-tw)/2 if align=='center' else 0)
            yy=y+i*step
            self.d.text((xx-bounds[0],yy-bounds[1]),line,font=font,fill=color,direction='rtl',language='ar')
            self.boxes.append((xx,yy,xx+tw,yy+bounds[3]-bounds[1],x,y,x+w,y+h))
        return y+len(lines)*step
    def rule(self,x,y,w,color=BORDER): self.d.line((x,y,x+w,y),fill=color,width=3)
    def panel(self,box,title=None,color=RED):
        x,y,w,h=box; self.d.rectangle((x,y,x+w,y+h),outline=BORDER,width=2)
        if title:
            self.text(title,(x+30,y+20,w-60,65),38,True,color)
            self.rule(x+30,y+84,w-60,color)
            return x+32,y+106,w-64,h-130
        return x+32,y+25,w-64,h-50
    def save(self,path):
        for left,top,right,bottom,x,y,x2,y2 in self.boxes:
            if left<x-1 or top<y-1 or right>x2+1 or bottom>y2+1:
                raise RuntimeError('Text exceeded its measured box')
        self.image.save(path,optimize=True)

def masthead(c,brief,page):
    end=datetime.fromisoformat(brief['window_end']).astimezone(UAE)
    c.text('أغريغيت | النشرة الجيوسياسية والأمنية',(2100,34,1625,60),32,True)
    c.text(end.strftime('%Y-%m-%d  %H:%M')+' بتوقيت الإمارات',(115,34,1800,60),30,False,MUTED,'left')
    c.text('نموذج اصطناعي لا يمثل أخباراً حقيقية' if brief.get('sample') else 'تغطية آخر ست ساعات | التقارير منسوبة إلى مصادرها',
      (400,99,3040,62),32,True,RED,'center')
    c.rule(115,175,3610,INK)
    c.text('التحليل الآلي ليس تحققاً مستقلاً | التفاصيل والروابط في ملف المصادر',(650,2090,3075,56),29,False,MUTED)
    c.text(f'الصفحة {page} من 2',(115,2090,500,56),29,True,MUTED,'left')

def refs(event,index):
    names=' / '.join(s['source'] for s in event['sources'])
    return f'[{index}] {event["status_ar"]} | {names}'

def event_card(c,event,index,box,assessment=False):
    x,y,w,h=box
    severity,color=SEVERITY[event['severity']]
    c.d.rectangle((x+w-9,y,x+w,y+h-12),fill=color)
    w-=28
    c.text(REGIONS[event['region']]+' | '+severity,(x,y,w,48),29,True,color)
    yy=c.text(event['title_ar'],(x,y+52,w,115),38,True)
    yy=c.text(event['summary_ar'],(x,yy+10,w,160),32)
    if assessment and event.get('assessment_ar'):
        yy=c.text('تقدير تحليلي: '+event['assessment_ar'],(x,yy+10,w,100),30,False,BLUE)
    c.text(refs(event,index),(x,y+h-66,w,56),27,False,MUTED)

def stats(c,brief):
    events=brief['events']; health=brief['health']; active=sum(r.get('status') in ('active','social_only') for r in health)
    vals=[('أحداث مختارة',len(events)),('أولوية مرتفعة',sum(e['severity']=='high' for e in events)),
      ('مناطق ممثلة',len({e['region'] for e in events})),('مصادر مستجيبة',f'{active}/{len(health)}'),
      ('تقارير مدخلة',brief['input_count']),('مصادر اجتماعية',len({s['source'] for e in events for s in e['sources'] if s['kind']=='social'})),
      ('فترة التغطية','6 ساعات'),('تحقق مستقل','غير متاح')]
    width=3610/8
    for i,(label,value) in enumerate(vals):
        x=115+(7-i)*width
        if i<7: c.d.line((x,210,x,330),fill=BORDER,width=2)
        c.text(label,(x+10,202,width-20,50),29,True,MUTED,'center')
        c.text(str(value),(x+10,260,width-20,72),43,True,INK,'center')
    c.rule(115,350,3610,INK)

def bars(c,counts,box,color=RED):
    x,y,w,h=box; maximum=max(counts.values(),default=1)
    for i,(label,value) in enumerate(counts.most_common(7)):
        yy=y+i*85
        c.text(label,(x+w*.51,yy,w*.49,54),29,True)
        c.d.rectangle((x+80,yy+14,x+80+(w*.43-80)*value/maximum,yy+40),fill=color)
        c.text(str(value),(x,yy,65,54),31,True,color)

def page1(brief,path):
    c=Canvas(); masthead(c,brief,1); stats(c,brief); events=brief['events']
    # Same left/right columns, central lead + ledger, and three bottom panels as Gazette.
    left=c.panel((115,390,1037,1038),'التطورات الإقليمية',RED)
    right=c.panel((2688,390,1037,1038),'أبرز التطورات الأمنية والسياسية',BLUE)
    for box,selection in [(right,list(enumerate(events[1:3],2))),(left,list(enumerate(events[3:5],4)))]:
        x,y,w,h=box
        if not selection: c.text('لا توجد تقارير إضافية مستوفية للشروط في هذه النافذة.',(x,y,w,220),34,False,MUTED)
        for i,(index,event) in enumerate(selection): event_card(c,event,index,(x,y+i*455,w,430))
    x,y,w=1286,395,1344
    if events:
        lead=events[0]
        c.text(lead['title_ar'],(x,y,w,198),57,True)
        c.rule(x,y+203,w,GOLD)
        c.text(lead['summary_ar'],(x,y+233,w,300),38)
        c.text(refs(lead,1),(x,y+545,w,85),29,False,MUTED)
    else: c.text('لا توجد مواد مستوفية لشروط النشر في النافذة المحددة.',(x,y,w,280),51,True)
    ledger=c.panel((1286,1080,1344,348),'سجل المتابعة',GOLD)
    lx,ly,lw,lh=ledger
    for i,event in enumerate(events[5:8],6):
        c.text(f'[{i}] '+event['title_ar'],(lx,ly+(i-6)*68,lw,62),32,True)
    if len(events)<6: c.text('التغطية محدودة؛ لا يُستنتج غياب الأحداث من غياب التقارير.',ledger,33,False,MUTED)
    for box,label,color in [((115,1480,1114,530),'حالة المصادر',GOLD),((1382,1480,1114,530),'تصريحات ورصد اجتماعي',BLUE),((2688,1480,1037,530),'تقدير تحليلي وما يستحق المتابعة',RED)]:
        px,py,pw,ph=c.panel(box,label,color)
        if label=='حالة المصادر':
            healthy={r['region'] for r in brief['health'] if r.get('status') in ('active','social_only')}
            missing=[name for key,name in REGIONS.items() if key not in healthy]
            note='فجوات في المصادر المحلية: '+('، '.join(missing) if missing else 'استجابت مصادر في جميع المناطق.')
            c.text(note,(px,py,pw,235),33,False,MUTED)
            c.text('تاريخ الخبر وتوقيته محفوظان. الروابط والأدلة في ملف المصادر.',(px,py+250,pw,135),31)
        elif label=='تصريحات ورصد اجتماعي':
            social=[(i,e) for i,e in enumerate(events,1) if any(s['kind']=='social' for s in e['sources'])]
            note=' '.join(f'[{i}] '+e['summary_ar'] for i,e in social[:2]) or 'لا توجد مواد اجتماعية مؤهلة في هذه الطبعة. لا تُعامل إعادة النشر كتأكيد مستقل.'
            c.text(note,(px,py,pw,ph),34)
        else:
            note=(events[0].get('assessment_ar') or 'لا يتوفر تقدير مدعوم بالأدلة.') if events else 'لا تتوفر أدلة كافية لإصدار تقدير.'
            c.text('تقدير تحليلي: '+note,(px,py,pw,205),33,False,BLUE)
            watch=events[0].get('watch_ar') if events else ''
            c.text('للمتابعة: '+(watch or 'انتظار تحديثات موثقة من المصادر.'),(px,py+220,pw,175),33)
    c.save(path); return c.truncated

def page2(brief,path):
    c=Canvas(); masthead(c,brief,2); events=brief['events']
    # Gazette's second-page analytical columns now describe news evidence, never markets.
    c.text('توزيع التغطية ومصادر الأدلة',(115,205,3610,80),46,True)
    box=c.panel((115,330,1037,795),'أبرز المناطق الممثلة',RED)
    bars(c,Counter(REGIONS[e['region']] for e in events),box)
    box=c.panel((1286,330,1344,795),'متابعة التطورات',GOLD)
    x,y,w,h=box
    for row,(i,event) in enumerate(list(enumerate(events,1))[5:8]):
        c.text(f'[{i}] '+event['title_ar'],(x,y+row*208,w,112),34,True)
        c.text(event.get('watch_ar') or 'انتظار تحديث من المصدر.',(x,y+row*208+116,w,82),30,False,MUTED)
    if len(events)<6: c.text('لا توجد تطورات إضافية مؤهلة في هذه النافذة.',box,34,False,MUTED)
    box=c.panel((2688,330,1037,795),'أولوية الأخبار وحالة الإسناد',BLUE)
    x,y,w,h=box
    bars(c,Counter(SEVERITY[e['severity']][0] for e in events),(x,y,w,300),BLUE)
    c.text('الأولوية ترتيب تحريري، وليست احتمالاً رقمياً لوقوع حدث.',(x,y+290,w,140),32,False,MUTED)
    c.text('كل خبر منسوب إلى مصدره. عدد الناشرين لا يثبت استقلال الأدلة.',(x,y+450,w,170),34,True,RED)
    c.rule(115,1175,3610,INK)
    c.text('تحديثات إقليمية ومراجع النشرة',(115,1210,3610,80),44,True)
    for index,event in enumerate(events[6:12],7):
        row=(index-7)//2; col=(index-7)%2; x=2025 if col==0 else 115; y=1330+row*210
        c.text(f'[{index}] '+REGIONS[event['region']]+' — '+event['title_ar'],(x,y,1695,105),34,True)
        c.text(event['summary_ar'],(x,y+112,1695,82),31)
    if len(events)<7:
        c.text('لا تُضاف أخبار قديمة أو حشو لاستكمال مساحة الصفحة. راجع ملف المصادر للتفاصيل المتاحة.',(115,1360,3610,180),39,False,MUTED)
    c.text('جميع الروابط والنصوص الكاملة للملخصات مرفقة بملف المصادر. علامات الحذف تشير إلى اختصار بصري فقط.',
      (115,1990,3610,66),31,False,MUTED)
    c.save(path); return c.truncated

def render(brief,output):
    output=Path(output); output.mkdir(parents=True,exist_ok=True)
    paths=[output/'arabic-p1.png',output/'arabic-p2.png']
    truncations=page1(brief,paths[0])+page2(brief,paths[1])
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
