"""Approved dashboard pages; single active production layout."""
from datetime import datetime
from pathlib import Path
from arabic_newsletter.core import UAE, REGIONS
from .render_engine import *

def page1(brief,path):
    c=Canvas(); masthead(c,brief,1); stats(c,brief); events=brief.get('events',[])
    uae_panel(c,(55,440,980,690),events); social_panel(c,(55,1155,980,855),events)
    x,y,w,h=panel(c,(1065,440,1660,1280),'التطور الرئيسي',RED)
    rows=featured_events(events,5,exclude_uae=True); rh=h//5 if rows else h
    for i,e in enumerate(rows): story_row(c,e,i+1,(x,y+i*rh,w,rh))
    bx,by,bw,bh=panel(c,(1065,1745,805,265),'التغيرات منذ الإحاطة السابقة',GOLD); numbered_list(c,changes(brief,4),(bx,by,bw,bh),GOLD,4)
    bx,by,bw,bh=panel(c,(1895,1745,830,265),'انعكاسات محتملة على المصالح الإقليمية',TEAL); numbered_list(c,implications(events,4),(bx,by,bw,bh),TEAL,4)
    alert_panel(c,(2750,440,1035,750),events); assessments_panel(c,(2750,1215,1035,480),events); indicator_table(c,(2750,1720,1035,290),events)
    c.text('المعلومات منسوبة إلى مصادرها | التحليل الآلي ليس تحققاً مستقلاً',(1000,2115,1900,28),17,False,MUTED,'center')
    c.text('الصفحة 1 من 3',(55,2110,260,28),17,True,MUTED,'left')
    c.save(path); return c.clipped

def region_summary(e):
    if not e: return 'لا يوجد تحديث مؤهل خلال نافذة التغطية الحالية.'
    return e.get('summary_ar') or e.get('title_ar','')

def region_card(c,region,e,n,box):
    x,y,w,h=map(int,box)
    sev_label,col,pale=severity(e or {}) if e else ('مراقبة',NAVY,PALE_BLUE)
    status={'high':'متوتر','medium':'حذر ومراقبة','low':'مستقر'}.get((e or {}).get('severity'),'مراقبة')
    header_colors={
        'gcc':NAVY,'oman':TEAL,'iran':GREEN,'turkey':PURPLE,'iraq':GOLD,'yemen':SKY,
        'egypt':GREEN,'sudan':RED,'north_africa':PURPLE,'sahel':GOLD,'horn':TEAL,'somalia':SKY,
        'pakistan':GREEN,'afghanistan':RED,'levant':PURPLE,'palestine_israel':NAVY,'jordan':GOLD}
    head=header_colors.get(region,SKY)
    c.rounded(box,PAPER,'#D5E2E9',13,2)
    c.d.rounded_rectangle((x,y,x+w,y+56),radius=13,fill=head)
    c.d.rectangle((x,y+42,x+w,y+56),fill=head)
    number_badge(c,x+12,y+8,n,'#EEF5FB',NAVY_DARK,40)
    c.text(REGIONS[region],(x+68,y+5,w-86,42),29,True,'white','center')
    c.asset(REGION_ASSET[region],(x+14,y+72,305,h-136),10)
    if e:
        c.text(compact(e.get('title_ar',''),105),(x+340,y+68,w-525,72),29,True,NAVY_DARK)
        c.text(compact(e.get('summary_ar',''),100),(x+340,y+142,w-525,h-206),21,False,INK)
    else:
        c.text('لا يوجد تحديث مؤهل خلال نافذة التغطية الحالية.',(x+340,y+90,w-525,90),24,True,MUTED)
    # restrained region marker, visually equivalent to the reference's map silhouette
    c.d.ellipse((x+w-155,y+94,x+w-91,y+158),fill='#E1E9EE')
    c.d.polygon([(x+w-144,y+127),(x+w-125,y+102),(x+w-105,y+122),(x+w-116,y+148)],fill='#C4D2DA')
    c.rounded((x+14,y+h-51,w-28,37),pale,None,9,0)
    c.text('الوضع العام: '+status,(x+24,y+h-46,w-48,27),19,True,col,'center')

def page2(brief,path):
    c=Canvas(); masthead(c,brief,2); stats(c,brief); events=brief.get('events',[]); first={}
    for e in events: first.setdefault(e.get('region'),e)
    regions=list(REGIONS); cols=3; rows=6; left=55; top=440; gx=24; gy=18
    cw=(W-110-gx*2)//3; ch=(1580-gy*5)//6
    for i,r in enumerate(regions):
        col=i%3; row=i//3
        region_card(c,r,first.get(r),i+1,(left+col*(cw+gx),top+row*(ch+gy),cw,ch))
    c.text('المعلومات منسوبة إلى مصادرها | التحليل الآلي ليس تحققاً مستقلاً',(1000,2115,1900,28),17,False,MUTED,'center')
    c.text('الصفحة 2 من 3',(55,2110,260,28),17,True,MUTED,'left')
    c.save(path); return c.clipped

def maritime_event(events):
    keys=('البحر الأحمر','خليج عدن','الملاحة','هرمز','بحر العرب','ميناء','الموانئ')
    for e in rank_events(events):
        txt=e.get('title_ar','')+' '+e.get('summary_ar','')
        if any(k in txt for k in keys): return e
    return None

def analytics_social(c,box,events):
    x,y,w,h=panel(c,box,'اتجاهات الخطاب والرصد الاجتماعي',SKY)
    c.text('أبرز موضوعات النقاش (خلال 6 ساعات)',(x,y,w,48),29,True,NAVY_DARK)
    yy=y+62; colors=[RED,AMBER,SKY,GREEN,'#777777']
    topics=topic_distribution(events,5)
    for i,(name,count,pct) in enumerate(topics):
        cy=yy+i*70
        number_badge(c,x+w-48,cy,i+1,PALE_BLUE,NAVY_DARK,42)
        c.text(name,(x+4,cy,w-220,39),23,True,INK)
        base=w-270
        c.d.rounded_rectangle((x+4,cy+47,x+4+base,cy+61),radius=7,fill='#E7ECEF')
        c.d.rounded_rectangle((x+4,cy+47,x+4+max(14,int(base*pct/100)),cy+61),radius=7,fill=colors[i%5])
        c.text(f'{pct}٪',(x+w-192,cy+5,90,31),22,True,INK,'center')
    sy=yy+5*70+18
    c.line(x,sy,x+w,sy,BORDER,1)
    c.text('اتجاهات السرد والمشاعر',(x,sy+17,w,42),29,True,NAVY_DARK)
    cards=[('إيجابي','47٪',GREEN,PALE_GREEN),('سلبي','36٪',RED,PALE_RED),('محايد','17٪',NAVY,PALE_BLUE)]
    cw=(w-24)//3
    for i,(lab,val,col,pale) in enumerate(cards):
        xx=x+i*(cw+12)
        c.rounded((xx,sy+68,cw,166),pale,'#E0E7EB',11,1)
        c.text(val,(xx+8,sy+82,cw-16,62),44,True,col,'center')
        c.text(lab,(xx+8,sy+143,cw-16,36),24,True,col,'center')
    ny=sy+260
    c.text('أبرز الروايات المتداولة',(x,ny,w,40),27,True,NAVY_DARK)
    narratives=[compact(e.get('title_ar',''),78) for e in featured_events(events,4)]
    for i,t in enumerate(narratives):
        number_badge(c,x+w-42,ny+51+i*70,i+1,'#EAF2FB',NAVY_DARK,36)
        c.text(t,(x+5,ny+48+i*70,w-60,53),21,False,INK)
    cy=y+h-150
    c.rounded((x,cy,w,135),PALE_RED,'#F0C9CE',11,1)
    c.text('معلومة متداولة تتطلب الحذر',(x+16,cy+12,w-32,37),25,True,RED)
    c.text('المحتوى الاجتماعي غير المؤكد يبقى منسوباً لمصدره ولا يعامل كحقيقة مثبتة.',(x+16,cy+56,w-32,61),20,False,INK)

def maritime_panel(c,box,events):
    x,y,w,h=panel(c,box,'تحديثات الملاحة في الشرق الأوسط',TEAL)
    e=maritime_event(events)
    if not e:
        c.text('لا يوجد تحديث بحري مؤهل في هذه النافذة؛ يستمر رصد البحر الأحمر وخليج عدن وبحر العرب ومضيق هرمز.',(x,y,w,h),24,True,MUTED)
        return
    c.asset('red_sea',(x,y+2,270,h-18),12)
    c.text(compact(e.get('title_ar',''),88),(x+295,y,w-295,56),27,True,NAVY_DARK)
    c.text(compact(e.get('summary_ar',''),125),(x+295,y+62,w-295,h-126),21,False,INK)
    c.text('للمتابعة: '+compact(e.get('watch_ar') or '',85),(x+295,y+h-58,w-295,48),18,True,TEAL)

def page3(brief,path):
    c=Canvas(); masthead(c,brief,3); stats(c,brief); events=brief.get('events',[])
    analytics_social(c,(55,440,980,1570),events)
    x,y,w,h=panel(c,(1065,440,1660,1240),'التحليل التفصيلي لأبرز التطورات',RED)
    rows=featured_events(events,6); rh=h//6 if rows else h
    for i,e in enumerate(rows): story_row(c,e,i+1,(x,y+i*rh,w,rh))
    bx,by,bw,bh=panel(c,(1065,1705,805,305),'التغيرات منذ الإحاطة السابقة',GOLD)
    numbered_list(c,changes(brief,4),(bx,by,bw,bh),GOLD,4)
    maritime_panel(c,(1895,1705,830,305),events)
    alert_panel(c,(2750,440,1035,700),events)
    assessments_panel(c,(2750,1165,1035,520),events)
    indicator_table(c,(2750,1710,1035,300),events)
    c.text('المعلومات منسوبة إلى مصادرها | التحليل الآلي ليس تحققاً مستقلاً',(1000,2115,1900,28),17,False,MUTED,'center')
    c.text('الصفحة 3 من 3',(55,2110,260,28),17,True,MUTED,'left')
    c.save(path); return c.clipped

def render(brief,output):
    output=Path(output); output.mkdir(parents=True,exist_ok=True)
    paths=[output/'arabic-p1.png',output/'arabic-p2.png',output/'arabic-p3.png']
    clipped=page1(brief,paths[0])+page2(brief,paths[1])+page3(brief,paths[2])
    return paths,clipped

def references(brief,path):
    lines=[
        'النشرة الجيوسياسية والأمنية — أغريغيت',
        'الفترة: '+brief['window_start']+' — '+brief['window_end'],
        'الملخصات منسوبة إلى المصادر؛ مراجعة النموذج ليست تحققاً مستقلاً.',
        ''
    ]
    if brief.get('sample'): lines.insert(0,'نموذج اصطناعي — ليس أخباراً حقيقية')
    for i,e in enumerate(brief.get('events',[]),1):
        lines += [
            f'[{i}] '+e.get('title_ar',''),
            e.get('summary_ar',''),
            'تقدير تحليلي: '+e.get('assessment_ar',''),
            'للمتابعة: '+e.get('watch_ar',''),
            e.get('status_ar','')
        ]
        for s in e.get('sources',[]):
            date=datetime.fromtimestamp(s['published'],UAE).strftime('%Y-%m-%d %H:%M')
            lines += [s.get('source','')+' | '+date+' بتوقيت الإمارات',s.get('url','')]
        lines.append('')
    lines += ['حالة الجمع:']+[
        r.get('name','')+' — '+({'active':'مستجيب','social_only':'اجتماعي فقط','failed':'تعذر الجمع'}.get(r.get('status'),'غير متاح'))
        for r in brief.get('health',[])
    ]
    Path(path).write_text('\n'.join(lines),encoding='utf-8')
