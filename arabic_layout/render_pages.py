"""Three-page Arabic command briefing; typography-first and image-free."""
from datetime import datetime
from pathlib import Path
from arabic_newsletter.core import UAE, REGIONS
from .render_engine import *

def _footer(c,page):
    c.text('المعلومات منسوبة إلى مصادرها، والتحليل تقديري وليس تحققاً مستقلاً',(1110,2115,1620,28),18,True,MUTED,'center')
    c.text(f'الصفحة {page} من 3',(55,2112,260,30),18,True,MUTED,'left')

def _uae_panel(c,box,events):
    x,y,w,h=panel(c,box,'الإمارات، موقف داخلي وإقليمي',STEEL)
    items=[e for e in events if is_uae(e)][:3]
    if not items:
        c.text('لا يوجد تحديث إماراتي مؤهل خلال نافذة التغطية الحالية.',(x,y,w,h),29,True,MUTED)
        return
    step=h//len(items)
    for i,e in enumerate(items):
        yy=y+i*step
        c.text(compact(e.get('title_ar',''),92),(x,yy,w,60),30,True,INK)
        c.text(compact(e.get('summary_ar',''),145),(x,yy+66,w,step-74),24,False,INK)
        if i<len(items)-1: c.line(x,yy+step-4,x+w,yy+step-4,BORDER,1)

def _alert_panel(c,box,events):
    x,y,w,h=panel(c,box,'مؤشرات الإنذار والمتابعة',ALERT)
    items=rank_events(events)[:5]
    if not items:
        c.text('لا توجد مؤشرات مؤهلة.',(x,y,w,h),28,True,MUTED); return
    step=h//len(items)
    for i,e in enumerate(items):
        yy=y+i*step; label,col,pale=severity(e)
        c.rounded((x+w-132,yy+6,120,36),pale,None,8,0)
        c.text(label,(x+w-126,yy+11,108,25),18,True,col,'center')
        c.text(compact(e.get('title_ar',''),100),(x,yy,w-155,52),25,True,INK)
        c.text(compact(e.get('watch_ar',''),92),(x,yy+55,w,step-63),21,False,MUTED)
        if i<len(items)-1: c.line(x,yy+step-4,x+w,yy+step-4,BORDER,1)

def _assessment_panel(c,box,events):
    x,y,w,h=panel(c,box,'تقديرات أولية',OLIVE)
    vals=[e.get('assessment_ar') for e in rank_events(events) if e.get('assessment_ar')][:5]
    list_block(c,vals,(x,y,w,h),OLIVE,24,5)

def _source_mix_panel(c,box,brief):
    x,y,w,h=panel(c,box,'مزيج المصادر المستخدمة',BLUE,'توزيع لغات المصادر في الأحداث المؤهلة')
    rows=source_distribution(brief,6)
    if not rows:
        c.text('لم تُستخدم مصادر في أحداث مؤهلة خلال هذه الدورة.',(x,y,w,h),25,True,MUTED); return
    step=h//len(rows)
    for i,(name,count,pct) in enumerate(rows):
        yy=y+i*step
        c.text(name,(x,yy,w-235,34),23,True,INK)
        c.text(f'{count} مصدر، {pct}٪',(x+w-215,yy,195,34),20,True,BLUE,'center')
        base=w-235
        c.d.rounded_rectangle((x,yy+42,x+base,yy+54),radius=6,fill='#E1E6E3')
        c.d.rounded_rectangle((x,yy+42,x+max(12,int(base*pct/100)),yy+54),radius=6,fill=BLUE)

def page1(brief,path):
    c=Canvas(); masthead(c,brief,1); stats(c,brief); events=brief.get('events',[])
    _uae_panel(c,(55,420,930,650),events)
    bx,by,bw,bh=panel(c,(55,1090,930,390),'التغيرات منذ الإحاطة السابقة',SAND)
    list_block(c,changes(brief,5),(bx,by,bw,bh),SAND,23,5)
    _source_mix_panel(c,(55,1500,930,510),brief)

    x,y,w,h=panel(c,(1010,420,1740,1080),'أبرز التطورات',COMMAND,'مرتبة حسب الأهمية مع الحفاظ على التنوع الجغرافي')
    rows=featured_events(events,6,exclude_uae=True); rh=h//max(1,len(rows))
    for i,e in enumerate(rows): row_event(c,e,i+1,(x,y+i*rh,w,rh))
    bx,by,bw,bh=panel(c,(1010,1520,1740,490),'انعكاسات محتملة على الأمن الإقليمي',TEAL)
    list_block(c,implications(events,5),(bx,by,bw,bh),TEAL,25,5)

    _alert_panel(c,(2775,420,1010,780),events)
    _assessment_panel(c,(2775,1220,1010,790),events)
    _footer(c,1); c.save(path); return c.clipped

def _region_card(c,region,e,n,box):
    x,y,w,h=map(int,box); color=REGION_COLORS.get(region,STEEL)
    c.rounded(box,PAPER,'#C9D0CC',11,2)
    c.d.rectangle((x,y,x+w,y+54),fill=color)
    c.rounded((x+12,y+8,40,38),'#F4F6F4',None,7,0); c.center(str(n),x+32,y+27,18,True,color)
    c.text(REGIONS[region],(x+65,y+6,w-82,38),27,True,'#FFFFFF','center')
    if e:
        label,col,pale=severity(e)
        c.rounded((x+w-138,y+68,120,35),pale,None,7,0); c.text(label,(x+w-132,y+73,108,24),17,True,col,'center')
        c.text(compact(e.get('title_ar',''),96),(x+18,y+68,w-175,58),27,True,INK)
        c.text(compact(e.get('summary_ar',''),118),(x+18,y+132,w-36,h-178),22,False,INK)
        status='متوتر' if e.get('severity')=='high' else ('حذر ومراقبة' if e.get('severity')=='medium' else 'مستقر نسبياً')
    else:
        c.text('لا يوجد تحديث مؤهل خلال نافذة التغطية الحالية.',(x+18,y+92,w-36,88),23,True,MUTED)
        status='مراقبة'
    c.d.rectangle((x+14,y+h-36,x+w-14,y+h-14),fill='#EEF1EE')
    c.text('الوضع العام: '+status,(x+22,y+h-34,w-44,20),16,True,color,'center')

def page2(brief,path):
    c=Canvas(); masthead(c,brief,2); stats(c,brief); events=brief.get('events',[]); first={}
    for e in events: first.setdefault(e.get('region'),e)
    regions=list(REGIONS); left=55; top=420; gx=24; gy=16
    cw=(W-110-gx*2)//3; ch=(1585-gy*5)//6
    for i,r in enumerate(regions):
        col=i%3; row=i//3
        _region_card(c,r,first.get(r),i+1,(left+col*(cw+gx),top+row*(ch+gy),cw,ch))
    _footer(c,2); c.save(path); return c.clipped

def _analysis_text(c,box,title,text,color,subtitle=None):
    x,y,w,h=panel(c,box,title,color,subtitle)
    c.text(text or 'لا تتوافر مادة تحليلية كافية في هذه الدورة.',(x,y,w,h),30,False,INK,min_size=22,line_ratio=1.42)

def _watch_panel(c,box,items):
    x,y,w,h=panel(c,box,'مؤشرات المتابعة للدورة المقبلة',STEEL,'مؤشرات قابلة للملاحظة، لا توقعات قطعية')
    list_block(c,items,(x,y,w,h),STEEL,25,6)

def page3(brief,path):
    c=Canvas(); masthead(c,brief,3); stats(c,brief)
    events=brief.get('events',[]); a=brief.get('analysis') or {}
    # If the analytical model is unavailable, use evidence-bound event fields.
    situation=a.get('situation_ar') or ' '.join(e.get('assessment_ar','') for e in events[:4] if e.get('assessment_ar'))
    dynamics=a.get('dynamics_ar') or ' '.join(e.get('summary_ar','') for e in featured_events(events,4))
    cross=a.get('cross_region_ar') or ' '.join(e.get('assessment_ar','') for e in events[2:6] if e.get('assessment_ar'))
    implications_text=a.get('implications_ar') or ' '.join(implications(events,4))
    risk=a.get('risk_ar') or ' '.join(e.get('watch_ar','') for e in events[:4] if e.get('watch_ar'))
    watch=a.get('watch_ar') or [e.get('watch_ar','') for e in events if e.get('watch_ar')][:6]

    mode='إحاطة صباحية موسعة، تركيز على ما تراكم ليلاً وما قد يغير صورة اليوم' if brief.get('morning') else 'تحليل الدورة الحالية، مع فصل الوقائع عن التقدير'
    _analysis_text(c,(55,420,1840,520),'تقدير الموقف',situation,COMMAND,mode)
    _analysis_text(c,(1915,420,1870,520),'ديناميات التصعيد والتهدئة',dynamics,ALERT,'قراءة نمطية مبنية على الأحداث المؤهلة فقط')
    _analysis_text(c,(55,960,1840,500),'الترابط الإقليمي',cross,BLUE,'علاقات بين المسارات دون افتراض سببية غير مثبتة')
    _analysis_text(c,(1915,960,1870,500),'الانعكاسات المحتملة',implications_text,TEAL,'أمن إقليمي، بنية استراتيجية، دبلوماسية ووصول إنساني')
    _analysis_text(c,(55,1480,1840,530),'عدم اليقين والمخاطر البديلة',risk,OLIVE,'ما قد يضعف التقدير أو يغير اتجاهه')
    _watch_panel(c,(1915,1480,1870,530),watch)
    _footer(c,3); c.save(path); return c.clipped

def render(brief,output):
    output=Path(output); output.mkdir(parents=True,exist_ok=True)
    paths=[output/'arabic-p1.png',output/'arabic-p2.png',output/'arabic-p3.png']
    clipped=page1(brief,paths[0])+page2(brief,paths[1])+page3(brief,paths[2])
    return paths,clipped

def references(brief,path):
    lines=[
      'النشرة الأمنية والعسكرية — أغريغيت',
      'الفترة: '+brief['window_start']+' — '+brief['window_end'],
      'الملخصات منسوبة إلى المصادر، والتحليل تقديري وليس تحققاً مستقلاً.',
      ''
    ]
    if brief.get('sample'): lines.insert(0,'نموذج اصطناعي — ليس أخباراً حقيقية')
    for i,e in enumerate(brief.get('events',[]),1):
        lines += [f'[{i}] '+e.get('title_ar',''),e.get('summary_ar',''),
                  'تقدير: '+e.get('assessment_ar',''),'للمتابعة: '+e.get('watch_ar',''),e.get('status_ar','')]
        for s in e.get('sources',[]):
            date=datetime.fromtimestamp(s['published'],UAE).strftime('%Y-%m-%d %H:%M')
            lines += [s.get('source','')+'، '+date+' بتوقيت الإمارات',s.get('url','')]
        lines.append('')
    a=brief.get('analysis') or {}
    if a:
        lines += ['','المنتج التحليلي:']
        for key in ('situation_ar','dynamics_ar','cross_region_ar','implications_ar','risk_ar'):
            if a.get(key): lines.append(a[key])
        for item in a.get('watch_ar',[]): lines.append('• '+item)
    Path(path).write_text('\n'.join(lines),encoding='utf-8')
