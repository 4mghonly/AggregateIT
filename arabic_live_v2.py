"""AggregateIT Arabic Live V2 — reliability-first live briefing engine.

Design:
- no persistent SQLite across runs
- no cache
- no cross-run state
- no preflight probes
- no hard LLM dependency
- Arabic RSS is authoritative baseline
- source headline stays the visible headline
- source description stays the factual summary
- optional LLM enrichment may improve summaries/analysis, but failure never blocks publication
"""
from __future__ import annotations

import concurrent.futures
import email.utils
import html
import json
import os
import re
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlsplit

import feedparser
import requests

from arabic_newsletter.core import UAE, REGIONS, clean
from arabic_newsletter.render import render
from arabic_newsletter.delivery import send
from arabic_newsletter.core import State

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"arabic_newsletter"/"runtime"/"v2"
SOURCES=ROOT/"arabic_newsletter"/"sources.json"

REGION_WORDS={
 "gcc":("الإمارات","السعودية","قطر","الكويت","البحرين","الخليج","أبوظبي","دبي","الرياض","الدوحة"),
 "oman":("عُمان","عمان","مسقط"),
 "iran":("إيران","ايران","طهران","هرمز"),
 "turkey":("تركيا","أنقرة","انقرة"),
 "iraq":("العراق","بغداد","أربيل","اربيل","البصرة"),
 "yemen":("اليمن","صنعاء","عدن","الحوثي","الحوثيين"),
 "egypt":("مصر","القاهرة","سيناء","قناة السويس"),
 "sudan":("السودان","الخرطوم","دارفور","الفاشر"),
 "sahel":("مالي","النيجر","بوركينا","تشاد","موريتانيا","الساحل"),
 "north_africa":("ليبيا","تونس","الجزائر","المغرب","شمال أفريقيا"),
 "pakistan":("باكستان","إسلام آباد","اسلام آباد"),
 "afghanistan":("أفغانستان","افغانستان","كابل","طالبان"),
 "horn":("إثيوبيا","اثيوبيا","إريتريا","اريتريا","جيبوتي","القرن الأفريقي"),
 "somalia":("الصومال","مقديشو","صوماليلاند","بونتلاند"),
 "levant":("لبنان","بيروت","سوريا","دمشق"),
 "palestine_israel":("فلسطين","غزة","الضفة","القدس","إسرائيل","اسرائيل","تل أبيب","تل ابيب"),
 "jordan":("الأردن","الاردن","عمّان","عمان"),
}
SECURITY_WORDS=(
 "أمن","أمني","عسكري","الجيش","قوات","هجوم","غارة","قصف","صاروخ","مسيرة","مسيّرة","طائرة مسيرة",
 "حدود","اشتباك","مفاوض","هدنة","وقف إطلاق النار","وقف اطلاق النار","عقوبات","دبلوما","خارجية","دفاع",
 "إرهاب","ارهاب","احتلال","نزاع","حرب","مسلح","بحر الأحمر","البحر الأحمر","ممر ملاحي","ميناء","مجال جوي",
 "شرطة","طوارئ","دفاع مدني","تهديد","مقتل","إصابة","اصابة","رهائن","أسرى","اسرى","نازح","لاجئ"
)
EXCLUDE_WORDS=("رياضة","كرة القدم","مباراة","بورصة","أسهم","سهم","بيتكوين","عملات مشفرة","ترفيه","مهرجان","مطعم","فندق")

def is_arabic(text:str)->bool:
    letters=[c for c in text if c.isalpha()]
    return bool(letters) and sum("\u0600"<=c<="\u06ff" for c in letters)/len(letters)>=0.55

def strip_html(value)->str:
    value=html.unescape(str(value or ""))
    value=re.sub(r"<[^>]+>"," ",value)
    return clean(value)

def published_ts(entry)->float:
    for key in ("published_parsed","updated_parsed"):
        v=getattr(entry,key,None)
        if v:
            try: return datetime(*v[:6],tzinfo=timezone.utc).timestamp()
            except Exception: pass
    for key in ("published","updated"):
        raw=getattr(entry,key,None)
        if raw:
            try:
                dt=email.utils.parsedate_to_datetime(raw)
                if dt.tzinfo is None: dt=dt.replace(tzinfo=timezone.utc)
                return dt.timestamp()
            except Exception: pass
    return datetime.now(timezone.utc).timestamp()

def region_for(text:str,source_region:str)->str|None:
    scores={r:sum(1 for w in words if w in text) for r,words in REGION_WORDS.items()}
    ranked=sorted(scores.items(),key=lambda x:x[1],reverse=True)
    if ranked and ranked[0][1]>0:
        return ranked[0][0]
    return source_region if source_region in REGIONS else None

def relevant(text:str)->bool:
    if any(w in text for w in EXCLUDE_WORDS): return False
    return any(w in text for w in SECURITY_WORDS)

def load_sources():
    rows=json.loads(SOURCES.read_text(encoding="utf-8"))
    usable=[]
    for row in rows:
        if not row.get("enabled"): continue
        if row.get("verification_status")!="active": continue
        if row.get("language")!="ar": continue
        feed=(row.get("feed") or "").strip()
        if not feed.startswith("http"): continue
        usable.append(row)
    # Stable bounded source set; global Arabic outlets first, then regional.
    usable.sort(key=lambda r:(r.get("region")!="global",r.get("region",""),r.get("id","")))
    return usable[:36]

def fetch_source(src):
    try:
        r=requests.get(src["feed"],timeout=(5,10),headers={"User-Agent":"AggregateIT-Arabic-V2/1.0"})
        if r.status_code!=200: return [],{"source":src["name"],"status":f"http_{r.status_code}"}
        parsed=feedparser.parse(r.content)
        out=[]
        for entry in parsed.entries[:24]:
            title=strip_html(getattr(entry,"title",""))
            desc=strip_html(getattr(entry,"summary","") or getattr(entry,"description",""))
            link=str(getattr(entry,"link","") or "")
            text=(title+" "+desc).strip()
            if not title or not is_arabic(text) or not relevant(text): continue
            region=region_for(text,src.get("region"))
            if not region: continue
            out.append({
              "title":title[:100],
              "summary":desc[:650] if desc else title,
              "url":link,
              "source":src["name"],
              "source_id":src["id"],
              "country":src.get("country"),
              "region":region,
              "published":published_ts(entry),
            })
        return out,{"source":src["name"],"status":"ok","items":len(out)}
    except Exception as exc:
        return [],{"source":src["name"],"status":"error_"+type(exc).__name__}

def collect(hours=24):
    cutoff=(datetime.now(timezone.utc)-timedelta(hours=hours)).timestamp()
    sources=load_sources()
    items=[]; health=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        futures=[pool.submit(fetch_source,s) for s in sources]
        for fut in concurrent.futures.as_completed(futures):
            rows,h=fut.result(); health.append(h)
            items.extend(x for x in rows if x["published"]>=cutoff)
    # Deduplicate by normalized headline; preserve newest.
    seen=set(); dedup=[]
    for item in sorted(items,key=lambda x:x["published"],reverse=True):
        key=re.sub(r"\W+","",item["title"].casefold())
        if not key or key in seen: continue
        seen.add(key); dedup.append(item)
    return dedup,health

def select(items,limit=10):
    # Breadth first, then significance by recency and headline security density.
    by_region={}
    for x in items:
        by_region.setdefault(x["region"],[]).append(x)
    selected=[]
    for region in REGIONS:
        if by_region.get(region):
            selected.append(by_region[region][0])
            if len(selected)>=limit: break
    if len(selected)<limit:
        used={id(x) for x in selected}
        for x in items:
            if id(x) not in used:
                selected.append(x)
                if len(selected)>=limit: break
    return selected

def make_event(x,index):
    # Headline and first summary sentence remain bound to the same RSS item.
    title=clean(x["title"])[:100]
    summary=clean(x["summary"])[:620]
    if not summary:
        summary=title
    if title not in summary:
        summary=f"بحسب {x['source']}، {title}. "+summary
    return {
      "region":x["region"],"topic":"security",
      "title_ar":title,
      "summary_ar":summary[:700],
      "assessment_ar":"",
      "watch_ar":"",
      "severity":"medium",
      "status_ar":"تقرير منسوب",
      "fingerprint":f"v2-{index}-{x['source_id']}",
      "source_ids":[x["source_id"]],
      "sources":[{
        "id":x["source_id"],"source_id":x["source_id"],"source":x["source"],
        "url":x["url"],"published":x["published"],"affiliation":"publisher",
        "kind":"news","country":x.get("country"),"language":"ar","region":x["region"]
      }],
    }

def deterministic_analysis(events):
    counts=Counter(REGIONS.get(e["region"],e["region"]) for e in events)
    leading="، ".join(name for name,_ in counts.most_common(4))
    return {
      "situation_ar":f"تتركز المواد المؤهلة في هذه الدورة ضمن: {leading or 'عدة ساحات إقليمية'}. يعرض هذا الإصدار الوقائع المصدرية مباشرة من دون إضافة استنتاجات سببية غير مدعومة.",
      "implications_ar":"الأولوية هي متابعة ما إذا كانت التطورات الحالية تنتقل من مستوى التصريحات والتقارير الأولية إلى إجراءات رسمية أو ميدانية قابلة للرصد.",
      "developing_ar":["تطورات ميدانية أو دبلوماسية قد تتغير مع صدور تأكيدات رسمية إضافية."],
      "watch_ar":["بيانات رسمية جديدة، تغيرات في الوضع الميداني، أو قيود موثقة على الحدود والمجال الجوي والممرات البحرية."]
    }

def build_brief(items,health):
    chosen=select(items)
    events=[make_event(x,i) for i,x in enumerate(chosen)]
    now=datetime.now(timezone.utc).astimezone(UAE).replace(microsecond=0)
    start=now-timedelta(hours=24)
    regions={r:{"healthy_extractors":1 if any(e["region"]==r for e in events) else 0,"substitutes_used":0} for r in REGIONS}
    source_health={"regions":regions,"unresolved_regions":[r for r,v in regions.items() if not v["healthy_extractors"]]}
    coverage={
      "event_source_count":len({s["id"] for e in events for s in e["sources"]}),
      "event_source_languages":{"ar":len({s["id"] for e in events for s in e["sources"]})},
      "non_arabic_event_sources":0,
      "healthy_regions":[r for r,v in regions.items() if v["healthy_extractors"]],
      "active_extractors_by_region":{r:v["healthy_extractors"] for r,v in regions.items()},
      "substitutes_used":0,
      "unresolved_regions":source_health["unresolved_regions"],
      "coverage_degraded":bool(source_health["unresolved_regions"]),
    }
    return {
      "sample":False,"window_start":start.isoformat(),"window_end":now.isoformat(),
      "events":events,"input_count":len(items),"health":health,"rejected":[],
      "analysis":deterministic_analysis(events),"morning":now.hour<9,
      "coverage":coverage,"source_health":source_health,
      "empty_cycle":not bool(events),"previous_events":[]
    }

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    print("V2 stage=collect_start",flush=True)
    items,health=collect(24)
    print(f"V2 stage=collect_complete items={len(items)}",flush=True)
    brief=build_brief(items,health)
    if not items:
        brief["analysis"]={
          "situation_ar":"لم تُجمع مواد عربية مؤهلة ضمن نافذة الرصد الحالية. يُنشر هذا الإصدار حفاظاً على استمرارية المنتج مع الإشارة بوضوح إلى تراجع التغطية المصدرية.",
          "implications_ar":"لا ينبغي استنتاج غياب التطورات من غياب المواد المؤهلة؛ يستمر الرصد في الدورة التالية.",
          "developing_ar":["استعادة تدفق المصادر العربية المؤهلة والتحقق من عودة التغطية الإقليمية."],
          "watch_ar":["عودة خلاصات المصادر للعمل وظهور مواد مؤهلة جديدة ضمن النطاق."]
        }
    (OUT/"briefing.json").write_text(json.dumps(brief,ensure_ascii=False,indent=2),encoding="utf-8")
    print("V2 stage=render_start",flush=True)
    paths,_=render(brief,OUT)
    print("V2 stage=render_complete "+str([(p.name,p.stat().st_size) for p in paths]),flush=True)
    state=State(OUT/"state")
    try:
        edition="V2-"+brief["window_end"]
        print("V2 stage=discord_post_start",flush=True)
        receipt=send(state,edition,paths)
        print("V2 stage=complete receipt="+str(receipt),flush=True)
    finally:
        state.close()

if __name__=="__main__":
    main()
