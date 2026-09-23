"""Two-page Arabic policy briefing; low-clutter, evidence-first and image-free."""
from datetime import datetime
from pathlib import Path
from arabic_newsletter.core import UAE, REGIONS
from .render_engine import *

def _footer(c,page):
    c.text('المعلومات منسوبة إلى مصادرها، والتحليل تقديري وليس تحققاً مستقلاً',(1110,2115,1620,28),18,True,MUTED,'center')
    c.text(f'الصفحة {page} من 2',(55,2112,260,30),18,True,MUTED,'left')

def _event_key(e):
    return e.get('fingerprint') or sanitize_text(e.get('title_ar',''))

def layout_plan(brief):
    """Keep every visible story in exactly one news slot across the two pages."""
    events=list(brief.get('events') or [])
    uae=[e for e in events if is_uae(e)][:4]
    uae_keys={_event_key(e) for e in uae}
    non_uae=[e for e in events if _event_key(e) not in uae_keys]
    # The editorial model already returns events ranked by significance. Preserve
    # that ordering instead of re-sorting by region and accidentally promoting noise.
    leads=non_uae[:3]
    lead_keys={_event_key(e) for e in leads}
    secondary=[e for e in non_uae if _event_key(e) not in lead_keys][:6]
    return leads,secondary,uae

def _source_line(e,limit=3):
    names=[]
    for src in e.get('sources',[]):
        name=sanitize_text(src.get('source',''))
        lang=LANGUAGE_LABELS.get(src.get('language'),src.get('language') or '')
        label=(name+('، '+lang if lang else '')).strip('، ')
        if label and label not in names:
            names.append(label)
    if not names:
        return 'المصدر: غير متاح في العرض المختصر'
    return 'المصادر: '+' | '.join(names[:limit])

def _story_card(c,box,e,index,lead=False):
    x,y,w,h=map(int,box)
    _label,col,pale=severity(e)
    c.rounded(box,'#FCFAF5',BORDER,10,1)
    c.d.rectangle((x+w-8,y+8,x+w-2,y+h-8),fill=col)
    c.text(f'أولوية {index}' if lead else REGIONS.get(e.get('region'),'تطور إضافي'),
           (x+24,y+18,w-48,34),20,True,col)
    c.text(compact(e.get('title_ar',''),155 if lead else 135),
           (x+24,y+58,w-48,82),36 if lead else 30,True,INK,min_size=24)
    summary_limit=620 if lead else 420
    c.text(compact(e.get('summary_ar',''),summary_limit),
           (x+24,y+150,w-48,h-280 if lead else h-214),
           28 if lead else 24,False,INK,min_size=20,line_ratio=1.42)
    c.text(compact(_source_line(e),180),(x+24,y+h-112,w-48,34),18,True,MUTED,min_size=16)
    if lead:
        why=sanitize_text(e.get('assessment_ar',''))
        if why:
            c.text('لماذا يهم: '+compact(why,230),(x+24,y+h-70,w-48,48),20,True,col,min_size=17)

def _cycle_delta(brief):
    previous=brief.get('previous_events') or []
    current=brief.get('events') or []
    if not previous:
        return 'هذه أول مقارنة متاحة في سجل الإحاطات الحالية.'
    old={sanitize_text(e.get('title_ar','')) for e in previous}
    new=[e for e in current if sanitize_text(e.get('title_ar','')) not in old]
    regions=[]
    for e in new:
        name=REGIONS.get(e.get('region'))
        if name and name not in regions: regions.append(name)
    if not new:
        return 'لا توجد عناوين جديدة جوهرية مقارنة بالإحاطة السابقة؛ التركيز على تطور القصص القائمة.'
    region_text='، '.join(regions[:5])
    return f'{len(new)} تطورات جديدة مقارنة بالإحاطة السابقة' + (f'، أبرزها ضمن: {region_text}.' if region_text else '.')

def _uae_panel(c,box,brief,events):
    x,y,w,h=panel(c,box,'الإمارات | تغطية موسعة',GREEN if 'GREEN' in globals() else OLIVE,
                  'قيادة، دبلوماسية، سلامة عامة، طيران، حدود وبنية استراتيجية')
    if not events:
        c.text('لا يوجد تحديث إماراتي مؤهل في النافذة الحالية. يستمر الرصد للمصادر الرسمية والمحلية دون ملء المساحة بمحتوى روتيني.',
               (x,y,w,150),29,True,MUTED)
        yy=y+190
    else:
        usable_h=h-170
        step=max(190,usable_h//len(events))
        yy=y
        for i,e in enumerate(events):
            col=REGION_COLORS.get('gcc',OLIVE)
            c.text(compact(e.get('title_ar',''),110),(x,yy,w,66),28,True,col,min_size=23)
            c.text(compact(e.get('summary_ar',''),300),(x,yy+72,w,step-118),23,False,INK,min_size=19,line_ratio=1.38)
            c.text(compact(_source_line(e,2),120),(x,yy+step-38,w,26),16,True,MUTED,min_size=14)
            if i<len(events)-1: c.line(x,yy+step-5,x+w,yy+step-5,BORDER,1)
            yy+=step
    # Preserve the requested "changes since last briefing" signal without
    # repeating the same headlines in another card.
    note_y=y+h-126
    c.line(x,note_y-12,x+w,note_y-12,SAND,2)
    c.text('منذ الإحاطة السابقة',(x,note_y,w,28),18,True,SAND)
    c.text(_cycle_delta(brief),(x,note_y+34,w,72),18,False,MUTED,min_size=16)

def _analysis_panel(c,box,brief):
    a=brief.get('analysis') or {}
    x,y,w,h=panel(c,box,'التقدير التنفيذي',ALERT,
                  'قراءة لما تعنيه الوقائع مجتمعة، من دون إعادة سرد العناوين')
    situation=sanitize_text(a.get('situation_ar',''))
    implications_text=sanitize_text(a.get('implications_ar',''))
    text=situation
    if implications_text:
        text+=((' ' if text else '')+'الانعكاس المحتمل: '+implications_text)
    if not text:
        vals=[sanitize_text(e.get('assessment_ar','')) for e in brief.get('events',[]) if e.get('assessment_ar')]
        text=' '.join(vals[:5])
    c.text(text or 'لا تتوافر مادة تحليلية كافية في هذه الدورة.',(x,y,w,h),29,False,INK,min_size=21,line_ratio=1.45)

def _developing_items(brief):
    a=brief.get('analysis') or {}
    vals=a.get('developing_ar') or []
    if isinstance(vals,list):
        vals=[sanitize_text(v) for v in vals if sanitize_text(v)]
    else:
        vals=[]
    if vals:
        return vals[:5]
    # Evidence-bound fallback: use watch statements with region labels, never
    # repeat event titles or summaries verbatim.
    out=[]
    for e in brief.get('events',[]):
        watch=sanitize_text(e.get('watch_ar',''))
        if watch:
            item=REGIONS.get(e.get('region'),'إقليمي')+': '+watch
            if item not in out: out.append(item)
        if len(out)>=5: break
    return out

def _developing_panel(c,box,brief):
    x,y,w,h=panel(c,box,'قصص قيد التطور',SAND,
                  'مسارات لم تُحسم بعد؛ صياغة مختلفة عن عناوين الأخبار')
    list_block(c,_developing_items(brief),(x,y,w,h),SAND,23,5)

def _watch_panel(c,box,brief):
    a=brief.get('analysis') or {}
    items=a.get('watch_ar') or []
    if not isinstance(items,list): items=[]
    items=[sanitize_text(v) for v in items if sanitize_text(v)]
    if not items:
        items=[sanitize_text(e.get('watch_ar','')) for e in brief.get('events',[]) if e.get('watch_ar')]
    x,y,w,h=panel(c,box,'ما يجب مراقبته',BLUE,
                  'مؤشرات قابلة للملاحظة في الدورة المقبلة، لا توقعات قطعية')
    list_block(c,items,(x,y,w,h),BLUE,23,6)

def page2_region_plan(events):
    first={}
    for e in events:
        region=e.get('region')
        if region in REGIONS and region not in first: first[region]=e
    active=[r for r in REGIONS if r in first]
    quiet=[r for r in REGIONS if r not in first]
    return active,quiet,first

def _coverage_panel(c,box,events):
    active,quiet,_=page2_region_plan(events)
    x,y,w,h=panel(c,box,'التغطية الإقليمية',STEEL,
                  'المؤشر يعني وجود مادة مؤهلة في الدورة، وليس قياساً لمستوى الخطر')
    ordered=active+quiet
    cols=6; gap=12
    rows=(len(ordered)+cols-1)//cols
    cw=(w-gap*(cols-1))//cols
    ch=max(64,(h-gap*(rows-1))//rows)
    for i,region in enumerate(ordered):
        row=i//cols; col=i%cols; xx=x+col*(cw+gap); yy=y+row*(ch+gap)
        active_now=region in active
        color=REGION_COLORS.get(region,STEEL)
        c.rounded((xx,yy,cw,ch),'#F8F6F0',color if active_now else BORDER,8,1)
        c.text(REGIONS[region],(xx+8,yy+8,cw-16,26),17,True,color if active_now else MUTED,'center',min_size=14)
        c.text('مادة مؤهلة' if active_now else 'مراقبة',(xx+8,yy+38,cw-16,22),14,False,color if active_now else MUTED,'center',min_size=12)

def page1(brief,path):
    c=Canvas(); masthead(c,brief,1); stats(c,brief)
    leads,secondary,uae=layout_plan(brief)

    # Only two dominant information blocks: expanded UAE coverage and three
    # substantial lead stories. No repeated alert/assessment boxes.
    _uae_panel(c,(55,330,1170,1745),brief,uae)

    x,y,w,h=panel(c,(1250,330,2535,1745),'أبرز ما يهم اليوم',ALERT,
                  'ثلاثة تطورات مختارة، كل قصة تظهر مرة واحدة فقط')
    if not leads:
        c.text('لا توجد تطورات رئيسية مؤهلة بعد التحقق التحريري في النافذة الحالية.',(x,y,w,h),34,True,MUTED,'center')
    else:
        gap=18
        rh=(h-gap*(len(leads)-1))//len(leads)
        for i,e in enumerate(leads,1):
            _story_card(c,(x,y+(i-1)*(rh+gap),w,rh),e,i,True)

    _footer(c,1); c.save(path); return c.clipped

def page2(brief,path):
    c=Canvas(); masthead(c,brief,2); stats(c,brief)
    leads,secondary,uae=layout_plan(brief)

    # Left: secondary news that did NOT appear on page 1.
    x,y,w,h=panel(c,(55,330,2265,1250),'تطورات إضافية تستحق الانتباه',BLUE,
                  'أحداث ثانوية مختارة، من دون إعادة أي قصة من الصفحة الأولى')
    if not secondary:
        c.text('لا توجد تطورات إضافية مؤهلة في هذه الدورة.',(x,y,w,h),30,True,MUTED,'center')
    else:
        gap=12
        rh=(h-gap*(len(secondary)-1))//len(secondary)
        for i,e in enumerate(secondary,1):
            _story_card(c,(x,y+(i-1)*(rh+gap),w,rh),e,i,False)
    _coverage_panel(c,(55,1605,2265,470),brief.get('events',[]))

    # Right: three different policy-maker functions, not three versions of the
    # same event recap.
    _analysis_panel(c,(2345,330,1440,620),brief)
    _developing_panel(c,(2345,975,1440,510),brief)
    _watch_panel(c,(2345,1510,1440,565),brief)

    _footer(c,2); c.save(path); return c.clipped

def render(brief,output):
    output=Path(output); output.mkdir(parents=True,exist_ok=True)
    paths=[output/'arabic-p1.png',output/'arabic-p2.png']
    clipped=page1(brief,paths[0])+page2(brief,paths[1])
    return paths,clipped

def references(brief,path):
    lines=[
      'النشرة الجيوسياسية والأمنية — أغريغيت',
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
        for item in a.get('developing_ar',[]): lines.append('قيد التطور: '+item)
        for item in a.get('watch_ar',[]): lines.append('للمراقبة: '+item)
    Path(path).write_text('\n'.join(lines),encoding='utf-8')
