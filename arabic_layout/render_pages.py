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
    c.d.rectangle((x,y,x+w,y+58),fill=color)
    c.rounded((x+12,y+10,40,38),'#F4F6F4',None,7,0); c.center(str(n),x+32,y+29,18,True,color)
    c.text(REGIONS[region],(x+65,y+8,w-82,38),28,True,'#FFFFFF','center')
    if e:
        label,col,pale=severity(e)
        c.rounded((x+w-144,y+76,126,38),pale,None,7,0); c.text(label,(x+w-138,y+81,114,26),18,True,col,'center')
        c.text(compact(e.get('title_ar',''),120),(x+18,y+74,w-184,74),30,True,INK)
        source_names=[]
        for src in e.get('sources',[]):
            name=src.get('source')
            lang=LANGUAGE_LABELS.get(src.get('language'),src.get('language') or '')
            label_src=(name+'، '+lang).strip('، ')
            if label_src and label_src not in source_names: source_names.append(label_src)
        source_line='المصادر: '+' | '.join(source_names[:3]) if source_names else 'المصادر: غير متاحة في العرض المختصر'
        c.text(compact(e.get('summary_ar',''),250),(x+18,y+158,w-36,max(96,h-278)),25,False,INK,min_size=20,line_ratio=1.36)
        c.text(compact(source_line,150),(x+18,y+h-94,w-36,38),19,True,MUTED,min_size=17)
        status='متوتر' if e.get('severity')=='high' else ('حذر ومراقبة' if e.get('severity')=='medium' else 'مستقر نسبياً')
    else:
        status='مراقبة'
    c.d.rectangle((x+14,y+h-40,x+w-14,y+h-14),fill='#EEF1EE')
    c.text('الوضع العام: '+status,(x+22,y+h-38,w-44,22),17,True,color,'center')

def page2_region_plan(events):
    first={}
    for e in events:
        region=e.get('region')
        if region in REGIONS and region not in first: first[region]=e
    ranked=rank_events(list(first.values()))
    active=[e.get('region') for e in ranked if e.get('region') in REGIONS][:9]
    quiet=[r for r in REGIONS if r not in active]
    return active,quiet,first

def _coverage_strip(c,box,active,quiet):
    x,y,w,h=panel(c,box,'التغطية الإقليمية الكاملة',STEEL,'المناطق غير المعروضة أعلاه ما زالت تحت المراقبة حتى دون تطور مؤهل')
    ordered=active+quiet
    cols=6; gap=12
    rows=(len(ordered)+cols-1)//cols
    cw=(w-gap*(cols-1))//cols
    ch=(h-gap*(rows-1))//rows
    for i,region in enumerate(ordered):
        row=i//cols; col=i%cols; xx=x+col*(cw+gap); yy=y+row*(ch+gap)
        is_active=region in active
        color=REGION_COLORS.get(region,STEEL)
        c.rounded((xx,yy,cw,ch),PALE_BLUE if is_active else '#F3F5F3',color if is_active else BORDER,9,2 if is_active else 1)
        c.text(REGIONS[region],(xx+10,yy+8,cw-20,30),20,True,color if is_active else MUTED,'center',min_size=17)
        c.text('تطور مؤهل' if is_active else 'مراقبة مستمرة',(xx+10,yy+40,cw-20,24),15,True,color if is_active else MUTED,'center',min_size=14)

def page2(brief,path):
    c=Canvas(); masthead(c,brief,2); stats(c,brief); events=brief.get('events',[])
    active,quiet,first=page2_region_plan(events)
    # Use the canvas for evidence, not empty placeholders. Up to nine active regions
    # receive large cards; all 17 regions remain visible in the compact coverage strip.
    left=55; top=420; gx=24; gy=18; active_h=1110
    if active:
        cols=3; rows=(len(active)+cols-1)//cols
        cw=(W-110-gx*(cols-1))//cols
        ch=(active_h-gy*(rows-1))//rows
        for i,r in enumerate(active):
            col=i%cols; row=i//cols
            _region_card(c,r,first[r],i+1,(left+col*(cw+gx),top+row*(ch+gy),cw,ch))
    else:
        bx,by,bw,bh=panel(c,(55,420,W-110,1110),'المشهد الإقليمي',COMMAND)
        c.text('لا توجد تطورات مؤهلة بعد تطبيق التحقق التحريري في نافذة التغطية الحالية.',(bx,by,bw,bh),34,True,MUTED,'center')
    _coverage_strip(c,(55,1555,W-110,455),active,quiet)
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
