"""Ink & Copper: opt-in 4K Arabic editorial briefing theme.

Presentation-only. Does not collect news, call an LLM or send to Discord.
Every narrative and source label comes from the validated briefing object.
"""
from datetime import datetime
from pathlib import Path
from PIL import Image, ImageDraw
from arabic_layout.render_engine import Canvas, W, H, compact
from arabic_newsletter.core import UAE, REGIONS

BG = "#E9E7E3"
PAPER = "#FBF9F5"
INK = "#212A32"
MUTED = "#5B6268"
COPPER = "#B27A56"
BORDER = "#D1C8BF"
BLACK = "#1F2932"
TINT = "#F0E8E1"
RED = "#A55E52"

class Page(Canvas):
    def __init__(self, brief, number, heading, subtitle):
        super().__init__()
        self.d.rectangle((0,0,W,H),fill=BG)
        self.d.rectangle((0,0,W,290),fill=BLACK)
        self.d.rectangle((0,283,W,290),fill=COPPER)
        self.text("AGGREGATEIT",(80,48,1250,83),74,True,PAPER,"left",58)
        self.text("موجز جيوسياسي وأمني",(85,148,1250,55),41,True,"#E0C2AA","left",34)
        self.text(heading,(1810,42,1900,100),79,True,PAPER,"right",60)
        self.text(subtitle,(1810,154,1900,65),34,False,"#E5DDD7","right",30)
        self.text(f"{number:02d} / 03",(85,233,400,46),34,True,PAPER,"left",30)
        stamp = brief.get("window_end","")
        try: stamp = datetime.fromisoformat(stamp).astimezone(UAE).strftime("%Y-%m-%d %H:%M UAE")
        except (ValueError,TypeError): stamp = "وقت الإصدار غير متاح"
        self.text(stamp,(2470,232,1210,45),30,True,"#E6D1BF","right",26)
        if brief.get("sample"):
            self.text("عينة اختبارية، ليست أخباراً مباشرة",(970,235,1740,40),28,True,"#F2BE9D","center",25)

    def section(self, x,y,w,h,title,accent=COPPER):
        self.rounded((x,y,w,h),PAPER,BORDER,26,2)
        self.d.rectangle((x+w-14,y+20,x+w-7,y+83),fill=accent)
        self.text(title,(x+30,y+21,w-75,66),48,True,INK,"right",38)
        self.line(x+36,y+102,x+w-36,y+102,BORDER,2)
        return (x+40,y+128,w-80,h-161)

    def body(self,s,box,size=38,bold=False,color=INK):
        self.text(compact(s,650),box,size,bold,color,"right",27,1.36)

    def footer(self,brief):
        self.line(80,2060,W-80,2060,BORDER,2)
        self.text("الوقائع منسوبة إلى مصادرها؛ التقدير التحليلي ليس تحققاً مستقلاً.",(950,2080,2810,42),28,False,MUTED,"right",23)
        self.text("AGGREGATEIT / INK & COPPER",(80,2080,860,45),26,True,MUTED,"left",23)

def _uae(e):
    if not isinstance(e,dict): return False
    for s in e.get("sources") or []:
        if isinstance(s,dict) and s.get("country")=="AE": return True
    text=str(e.get("title_ar") or "")
    return e.get("region")=="gcc" and any(x in text for x in ("الإمارات","أبوظبي","دبي"))

def _src(e):
    values=[]
    for s in e.get("sources") or []:
        if isinstance(s,dict) and s.get("source"):
            name=str(s["source"])
            if name not in values: values.append(name)
    return "، ".join(values[:2]) if values else "المصدر غير متاح"

def _tile(c, x,y,w,h,e, regional=False):
    c.rounded((x,y,w,h),PAPER,BORDER,22,2)
    c.d.rectangle((x+w-12,y+18,x+w-6,y+h-18),fill=COPPER)
    if e:
        region=REGIONS.get(e.get("region"),"المشهد الإقليمي")
        if regional: c.text(region,(x+30,y+15,w-80,45),32,True,COPPER,"right",28)
        c.text(compact(e.get("title_ar"),175),(x+38,y+(68 if regional else 32),w-91,132),44,True,INK,"right",34)
        c.body(e.get("summary_ar"),(x+42,y+(200 if regional else 174),w-99,max(75,h-(290 if regional else 270))),33,False,INK)
        c.text("المصدر: "+_src(e),(x+36,y+h-68,w-88,43),26,True,MUTED,"right",23)
    else:
        c.text("لا توجد وقائع مؤهلة لهذه الخانة في فترة التغطية.",(x+38,y+55,w-91,h-90),35,False,MUTED,"right",27)

def _delta(brief):
    events=brief.get("events") or []
    prev=brief.get("previous_events")
    if not isinstance(prev,list) or not prev:
        return "المقارنة مع الإصدار السابق غير متاحة؛ لا يُفترض أن العناوين الحالية أحداث جديدة."
    old={str(e.get("fingerprint") or e.get("title_ar") or "").strip() for e in prev if isinstance(e,dict)}
    novel=[e for e in events if str(e.get("fingerprint") or e.get("title_ar") or "").strip() not in old]
    return f"{len(novel)} من {len(events)} مواد لا تطابق سجل الإصدار السابق نصياً؛ اختلاف القوائم لا يثبت وقوع أحداث جديدة."

def page1(brief,path):
    c=Page(brief,1,"الإمارات والخليج","الأولويات الأساسية وما تغير منذ الإحاطة السابقة")
    events=list(brief.get("events") or [])
    domestic=[e for e in events if _uae(e)]
    gulf=[e for e in events if e.get("region") in ("gcc","oman") and e not in domestic]
    c.section(1950,345,1810,775,"الإمارات العربية المتحدة")
    if domestic:
        for i,e in enumerate(domestic[:2]):
            _tile(c,1990,475+i*296,1730,274,e)
    else:
        c.body("لم تُسجل مادة إماراتية مؤهلة ضمن نافذة الرصد. لا يدل ذلك على غياب التطورات.",(2010,540,1650,315),49)
    c.section(80,345,1810,775,"مجلس التعاون الخليجي وعُمان")
    for i,e in enumerate(gulf[:2]):
        _tile(c,120,475+i*296,1730,274,e)
    if not gulf:
        c.body("لا توجد وقائع خليجية إضافية مؤهلة لعرضها في هذا الإصدار.",(125,575,1675,210),43)
    c.section(1950,1160,1810,820,"أبرز التطورات منذ النشرة السابقة")
    c.body(_delta(brief),(2020,1325,1660,185),43,True)
    rest=[e for e in events if e not in domestic and e not in gulf]
    if rest:
        c.text("أهم تطور إقليمي في هذه الدورة",(2020,1590,1640,60),36,True,COPPER)
        c.body(rest[0].get("title_ar"),(2015,1670,1640,150),41,True)
        c.text("المصدر: "+_src(rest[0]),(2020,1880,1630,48),27,False,MUTED)
    c.section(80,1160,1810,820,"سجل التغطية والمصادر")
    coverage=brief.get("coverage") or {}
    rows=[
        ("الأحداث المعروضة",str(len(events))),
        ("المصادر المستخدمة",str(coverage.get("event_source_count","غير متاح"))),
        ("الأقاليم النشطة",str(len({e.get("region") for e in events if e.get("region") in REGIONS}))),
        ("نافذة الرصد",str(brief.get("window_hours") or 6)+" ساعات"),
    ]
    for i,(label,value) in enumerate(rows):
        yy=1325+i*151
        c.text(label,(1010,yy,770,57),38,True,MUTED)
        c.text(value,(145,yy,790,65),45,True,INK,"left")
        c.line(145,yy+88,1790,yy+88,BORDER,1)
    c.footer(brief);c.save(path);return c.clipped

def page2(brief,path):
    c=Page(brief,2,"المشهد الإقليمي","تغطية متعددة المناطق حسب الوقائع المؤهلة وأهميتها")
    events=[e for e in brief.get("events") or [] if not _uae(e) and e.get("region") not in ("gcc","oman")]
    chosen=[]; used=set()
    for e in events:
        reg=e.get("region")
        if reg and reg not in used: chosen.append(e); used.add(reg)
        if len(chosen)==6: break
    for i in range(6):
        e=chosen[i] if i<len(chosen) else None
        x=1950 if i%2==0 else 80
        y=350+(i//2)*518
        _tile(c,x,y,1810,475,e,regional=True)
    active={e.get("region") for e in brief.get("events") or []}
    quiet=[REGIONS[k] for k in REGIONS if k not in active]
    c.rounded((80,1940,3680,112),TINT,BORDER,18,1)
    foot="نطاق الرصد الكامل: "+ "، ".join(REGIONS.values()) if not quiet else "مناطق بلا مواد مؤهلة هذه الدورة: "+ "، ".join(quiet)
    c.text(compact(foot,240),(135,1963,3570,65),30,True,INK,"right",24)
    c.footer(brief);c.save(path);return c.clipped

def _list(c,items,x,y,w,h,max_items=4):
    if isinstance(items,str): items=[items] if items else []
    if not isinstance(items,list): items=[]
    lines=[str(s) for s in items if str(s).strip()][:max_items]
    if not lines: lines=["المعلومات التحليلية غير متاحة لهذه الفترة."]
    step=max(110,(h-10)//max(1,len(lines)))
    for i,s in enumerate(lines):
        yy=y+i*step
        c.d.ellipse((x+w-17,yy+18,x+w-4,yy+31),fill=COPPER)
        c.body(s,(x+5,yy,w-52,step-15),32)

def page3(brief,path):
    c=Page(brief,3,"التحليل والتقدير","تفسير مستقل للوقائع مع بيان حدود الأدلة")
    a=brief.get("analysis") or {}
    x,y,w,h=c.section(1950,350,1810,760,"تقدير الموقف")
    c.body(a.get("situation_ar") or "لم يتوفر تقدير تحليلي.",(x,y+8,w,h-38),44)
    x,y,w,h=c.section(80,350,1810,760,"الدلالات والآثار المحتملة")
    c.body(a.get("implications_ar") or "لا توجد معطيات كافية لتحديد التداعيات.",(x,y+8,w,h-38),44)
    x,y,w,h=c.section(1950,1150,1810,805,"مؤشرات للمتابعة المبكرة")
    _list(c,a.get("watch_ar"),x,y,w,h,5)
    x,y,w,h=c.section(80,1150,1810,805,"الملفات قيد التطور والفجوات")
    _list(c,a.get("developing_ar"),x,y,w,h,4)
    status=(brief.get("llm_health") or {}).get("status","غير متاح")
    coverage=brief.get("coverage") or {}
    unresolved=coverage.get("unresolved_regions") or []
    c.text("حالة التحليل: "+str(status)+"  |  أقاليم دون تغطية كافية: "+str(len(unresolved)),(120,1976,3500,56),28,True,MUTED,"right",23)
    c.footer(brief);c.save(path);return c.clipped

def render(brief,output):
    path=Path(output);path.mkdir(parents=True,exist_ok=True)
    pages=[path/"arabic-p1.png",path/"arabic-p2.png",path/"arabic-p3.png"]
    clipped=page1(brief,pages[0])+page2(brief,pages[1])+page3(brief,pages[2])
    return pages,clipped
