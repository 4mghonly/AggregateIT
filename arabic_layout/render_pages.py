"""Three-page Arabic policy briefing; low-clutter, evidence-first and image-free."""
from datetime import datetime
from pathlib import Path
from arabic_newsletter.core import UAE, REGIONS
from .render_engine import *

def _footer(c,page):
    c.text('المعلومات منسوبة إلى مصادرها، والتحليل تقديري وليس تحققاً مستقلاً',(1040,2108,1760,34),21,True,MUTED,'center',min_size=19,line_ratio=1.15)
    c.text(f'الصفحة {page} من 3',(55,2108,300,34),21,True,MUTED,'left',min_size=19,line_ratio=1.15)

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
    secondary=[e for e in non_uae if _event_key(e) not in lead_keys][:3]
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
    c.rounded(box,PANEL_ALT,BORDER,10,1)
    c.d.rectangle((x+w-8,y+8,x+w-2,y+h-8),fill=col)
    c.text(f'أولوية {index}' if lead else REGIONS.get(e.get('region'),'تطور إضافي'),
           (x+24,y+14,w-48,40),24,True,col,min_size=21,line_ratio=1.15)
    c.text(compact(e.get('title_ar',''),155 if lead else 135),
           (x+24,y+56,w-48,102),42 if lead else 36,True,INK,min_size=29,line_ratio=1.20)
    summary_limit=620 if lead else 420
    c.text(compact(e.get('summary_ar',''),summary_limit),
           (x+24,y+168,w-48,h-300 if lead else h-232),
           33 if lead else 29,False,INK,min_size=25,line_ratio=1.30)
    c.text(compact(_source_line(e),145),(x+24,y+h-112,w-48,38),21,True,MUTED,min_size=19,line_ratio=1.16)
    if lead:
        why=sanitize_text(e.get('assessment_ar',''))
        if why:
            c.text('لماذا يهم: '+compact(why,185),(x+24,y+h-70,w-48,50),24,True,col,min_size=20,line_ratio=1.20)

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
    x,y,w,h=panel(c,box,'الإمارات | تغطية موسعة',OLIVE,
                  'قيادة، دبلوماسية، سلامة عامة، طيران، حدود وبنية استراتيجية')
    if not events:
        c.text('لا يوجد تحديث إماراتي مؤهل في النافذة الحالية. يستمر الرصد للمصادر الرسمية والمحلية دون ملء المساحة بمحتوى روتيني.',
               (x,y,w,160),33,True,MUTED,min_size=27,line_ratio=1.25)
        yy=y+190
    else:
        usable_h=h-170
        step=max(190,usable_h//len(events))
        yy=y
        for i,e in enumerate(events):
            col=REGION_COLORS.get('gcc',OLIVE)
            c.text(compact(e.get('title_ar',''),90),(x,yy,w,74),33,True,col,min_size=27,line_ratio=1.20)
            c.text(compact(e.get('summary_ar',''),235),(x,yy+80,w,step-130),28,False,INK,min_size=23,line_ratio=1.28)
            c.text(compact(_source_line(e,2),96),(x,yy+step-42,w,32),19,True,MUTED,min_size=17,line_ratio=1.16)
            if i<len(events)-1: c.line(x,yy+step-5,x+w,yy+step-5,BORDER,1)
            yy+=step
    # Preserve the requested "changes since last briefing" signal without
    # repeating the same headlines in another card.
    note_y=y+h-126
    c.line(x,note_y-12,x+w,note_y-12,SAND,2)
    c.text('منذ الإحاطة السابقة',(x,note_y,w,32),22,True,SAND,min_size=20,line_ratio=1.15)
    c.text(_cycle_delta(brief),(x,note_y+36,w,70),21,True,MUTED,min_size=18,line_ratio=1.20)

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
    c.text(text or 'لا تتوافر مادة تحليلية كافية في هذه الدورة.',(x,y,w,h),34,False,INK,min_size=26,line_ratio=1.32)

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
    list_block(c,_developing_items(brief),(x,y,w,h),SAND,27,5)

def _watch_panel(c,box,brief):
    a=brief.get('analysis') or {}
    items=a.get('watch_ar') or []
    if not isinstance(items,list): items=[]
    items=[sanitize_text(v) for v in items if sanitize_text(v)]
    if not items:
        items=[sanitize_text(e.get('watch_ar','')) for e in brief.get('events',[]) if e.get('watch_ar')]
    x,y,w,h=panel(c,box,'ما يجب مراقبته',BLUE,
                  'مؤشرات قابلة للملاحظة في الدورة المقبلة، لا توقعات قطعية')
    list_block(c,items,(x,y,w,h),BLUE,27,6)

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
        c.rounded((xx,yy,cw,ch),PANEL_ALT,color if active_now else BORDER,8,1)
        c.text(REGIONS[region],(xx+8,yy+5,cw-16,32),20,True,color if active_now else MUTED,'center',min_size=17,line_ratio=1.12)
        c.text('مادة مؤهلة' if active_now else 'مراقبة',(xx+8,yy+38,cw-16,26),17,True,color if active_now else MUTED,'center',min_size=15,line_ratio=1.12)

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

def _continuity_events(brief):
    """Current events first, then prior-edition events to keep page 3 populated."""
    out=[]; seen=set()
    for e in list(brief.get('events') or [])+list(brief.get('previous_events') or []):
        if not isinstance(e,dict): continue
        key=_event_key(e)
        if not key or key in seen: continue
        seen.add(key); out.append(e)
    return out

def _event_text(e):
    return sanitize_text(' '.join(str(e.get(k,'')) for k in ('title_ar','summary_ar','assessment_ar','watch_ar')))

def _first_matching(events,predicate):
    for e in events:
        if predicate(e): return e
    return None

def _brief_line(e,limit=220):
    if not e: return 'تستمر المتابعة من خلال المصادر الإقليمية النشطة مع إبقاء القصة الأعلى أولوية قيد الرصد.'
    text=sanitize_text(e.get('summary_ar') or e.get('title_ar') or '')
    return compact(text,limit)

def _page3_stats(c,brief,events):
    militant_terms=('الحوث','حماس','الجهاد الإسلامي','حزب الله','الشباب','داعش','القاعدة','طالبان','فصائل','ميليش')
    maritime_terms=('البحر الأحمر','باب المندب','هرمز','الخليج','خليج عدن','الملاحة','بحري','ساحل','ميناء','المتوسط')
    militant=sum(any(t in _event_text(e) for t in militant_terms) for e in events)
    maritime=sum(any(t in _event_text(e) for t in maritime_terms) for e in events)
    conflicts=sum(e.get('topic') in ('military','security','humanitarian_conflict') for e in events)
    vals=[('أقاليم رئيسية',len(REGIONS),BLUE),('جماعات مسلحة',max(1,militant),OLIVE),
          ('نزاعات',max(1,conflicts),ALERT),('توترات بحرية',max(1,maritime),SAND)]
    margin=55; gap=18; y=190; h=108; cw=(W-2*margin-gap*3)//4
    for i,(label,val,color) in enumerate(vals):
        x=margin+i*(cw+gap)
        c.rounded((x,y,cw,h),PAPER,BORDER,10,1)
        c.d.rectangle((x+cw-7,y+8,x+cw-2,y+h-8),fill=color)
        c.text(label,(x+24,y+13,cw-48,34),23,True,MUTED,'center',min_size=21,line_ratio=1.15)
        c.text(str(val),(x+24,y+50,cw-48,48),35,True,INK,'center',min_size=31,line_ratio=1.15)

def _category_rows(c,box,title,subtitle,color,rows):
    x,y,w,h=panel(c,box,title,color,subtitle)
    rows=[(sanitize_text(a),sanitize_text(b)) for a,b in rows if sanitize_text(a) or sanitize_text(b)]
    if not rows:
        rows=[('متابعة مستمرة','تستمر المتابعة من خلال أفضل المصادر الإقليمية المتاحة.')]
    step=max(1,h//len(rows))
    for i,(head,body) in enumerate(rows):
        yy=y+i*step
        c.text(head,(x,yy,w,40),27,True,color,min_size=23,line_ratio=1.16)
        c.text(compact(body,190),(x,yy+44,w,step-56),24,False,INK,min_size=21,line_ratio=1.27)
        if i<len(rows)-1: c.line(x,yy+step-5,x+w,yy+step-5,BORDER,1)

def _geographic_rows(events):
    groups=[
      ('الخليج والجزيرة العربية',{'gcc','oman','yemen'}),
      ('المشرق وإيران',{'iran','iraq','levant','palestine_israel','jordan','turkey'}),
      ('شمال وشرق أفريقيا',{'egypt','sudan','sahel','north_africa','horn','somalia'}),
      ('جنوب ووسط آسيا',{'pakistan','afghanistan'}),
    ]
    return [(label,_brief_line(_first_matching(events,lambda e,regs=regs:e.get('region') in regs))) for label,regs in groups]

def _militant_rows(events):
    specs=[
      ('الحوثيون',('الحوث','أنصار الله')),
      ('حماس والفصائل في غزة',('حماس','الجهاد الإسلامي','الفصائل في غزة')),
      ('الفصائل المسلحة على المحور العراقي السوري',('فصائل','ميليش','الحشد','كتائب','عصائب')),
      ('حركة الشباب',('حركة الشباب','الشباب','الصومال')),
    ]
    rows=[]; used=set()
    for label,terms in specs:
        e=_first_matching(events,lambda ev,terms=terms:any(t in _event_text(ev) for t in terms))
        if e:
            used.add(_event_key(e)); rows.append((label,_brief_line(e)))
    # Always fill the panel with the strongest remaining armed/conflict stories.
    for e in events:
        if len(rows)>=4: break
        if _event_key(e) in used: continue
        if e.get('topic') in ('military','security','humanitarian_conflict'):
            rows.append((REGIONS.get(e.get('region'),'فاعل مسلح'),_brief_line(e))); used.add(_event_key(e))
    return rows[:4]

def _conflict_rows(events):
    preferred=[
      ('غزة',{'palestine_israel'}),
      ('السودان',{'sudan'}),
      ('اليمن / البحر الأحمر',{'yemen'}),
      ('الحدود العراقية السورية',{'iraq','levant'}),
    ]
    rows=[]; used=set()
    for label,regs in preferred:
        e=_first_matching(events,lambda ev,regs=regs:ev.get('region') in regs and ev.get('topic') in ('military','security','humanitarian_conflict','political_stability'))
        if e:
            used.add(_event_key(e)); rows.append((label,_brief_line(e)))
    for e in events:
        if len(rows)>=4: break
        if _event_key(e) in used: continue
        if e.get('topic') in ('military','security','humanitarian_conflict'):
            rows.append((REGIONS.get(e.get('region'),'نزاع إقليمي'),_brief_line(e))); used.add(_event_key(e))
    return rows[:4]

def _maritime_rows(events):
    specs=[
      ('البحر الأحمر وباب المندب',('البحر الأحمر','باب المندب')),
      ('مضيق هرمز والخليج',('هرمز','الخليج')),
      ('خليج عدن والسواحل الصومالية',('خليج عدن','السواحل الصومالية','الصومال')),
      ('شرق المتوسط',('المتوسط','لبنان','غزة')),
    ]
    rows=[]; used=set()
    for label,terms in specs:
        e=_first_matching(events,lambda ev,terms=terms:any(t in _event_text(ev) for t in terms))
        if e:
            rows.append((label,_brief_line(e))); used.add(_event_key(e))
    # If the current/prior cycle contains fewer explicit maritime stories,
    # retain the strongest related regional story instead of leaving empty space.
    for e in events:
        if len(rows)>=4: break
        if _event_key(e) in used: continue
        if e.get('region') in ('yemen','gcc','oman','somalia','horn','levant','palestine_israel'):
            rows.append((REGIONS.get(e.get('region'),'مسار بحري'),_brief_line(e))); used.add(_event_key(e))
    return rows[:4]

def page3(brief,path):
    c=Canvas(); masthead(c,brief,3)
    events=_continuity_events(brief)
    _page3_stats(c,brief,events)

    _category_rows(c,(55,330,1840,790),'الجماعات المسلحة',
                   'الجهات غير الحكومية الأكثر تأثيراً في الدورة الحالية',OLIVE,_militant_rows(events))
    _category_rows(c,(1915,330,1870,790),'الأقاليم الجغرافية',
                   'أين يتركز الثقل الإقليمي الآن',BLUE,_geographic_rows(events))
    _category_rows(c,(55,1145,1840,790),'التوترات البحرية',
                   'الممرات والمجالات البحرية التي تستحق الانتباه',SAND,_maritime_rows(events))
    _category_rows(c,(1915,1145,1870,790),'النزاعات',
                   'أبرز ساحات الصراع والمتغيرات المرتبطة بها',ALERT,_conflict_rows(events))

    # Slim executive continuity strip: continuing stories stay visible when they
    # remain the most consequential, even if they appeared in the prior edition.
    c.rounded((55,1958,W-110,118),PANEL_ALT,BORDER,9,1)
    c.text('الخلاصة التنفيذية',(W-560,1974,470,40),25,True,STEEL,min_size=22,line_ratio=1.15)
    c.text('استمرار القصة نفسها لا يقلل أهميتها إذا بقيت الأعلى تأثيراً.  •  التمييز مطلوب بين الضجيج الإعلامي والمؤشرات القابلة للرصد.  •  أولوية المتابعة: الجغرافيا، الفاعلون المسلحون، والنقاط البحرية الحساسة.',
           (160,1972,W-800,52),21,True,INK,min_size=18,line_ratio=1.18)
    _footer(c,3); c.save(path); return c.clipped


def render(brief,output):
    output=Path(output); output.mkdir(parents=True,exist_ok=True)
    paths=[output/'arabic-p1.png',output/'arabic-p2.png',output/'arabic-p3.png']
    clipped=page1(brief,paths[0])+page2(brief,paths[1])+page3(brief,paths[2])
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
