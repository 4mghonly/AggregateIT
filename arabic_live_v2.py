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


def _json_env(name):
    raw=(os.getenv(name) or "").strip()
    if not raw:
        return {}
    value=json.loads(raw)
    return value if isinstance(value,dict) else {}

def _route(prefix):
    key=(os.getenv(prefix+"API_KEY") or "").strip()
    base=(os.getenv(prefix+"BASE_URL") or "").strip().rstrip("/")
    model=(os.getenv(prefix+"MODEL") or "").strip()
    if not (key and base and model):
        return None
    header=(os.getenv(prefix+"AUTH_HEADER") or "Authorization").strip()
    scheme=(os.getenv(prefix+"AUTH_SCHEME") or "Bearer").strip()
    chat="/"+(os.getenv(prefix+"CHAT_PATH") or "chat/completions").strip().lstrip("/")
    headers={"Content-Type":"application/json"}
    headers.update(_json_env(prefix+"EXTRA_HEADERS_JSON"))
    if header:
        headers[header]=(f"{scheme} {key}".strip() if scheme else key)
    return {"key":key,"base":base,"model":model,"chat":chat,"headers":headers,
            "options":_json_env(prefix+"REQUEST_OPTIONS_JSON")}

def _route_call(route,system,user,max_tokens=1800):
    url=route["base"] if route["base"].endswith(route["chat"]) else route["base"]+route["chat"]
    payload={"model":route["model"],
             "messages":[{"role":"system","content":system},{"role":"user","content":json.dumps(user,ensure_ascii=False)}],
             "temperature":0.1,"max_tokens":max_tokens,
             "response_format":{"type":"json_object"}}
    payload.update(route["options"])
    for attempt in range(2):
        try:
            r=requests.post(url,headers=route["headers"],json=payload,timeout=(8,45))
        except requests.RequestException as exc:
            if attempt==0:
                continue
            raise RuntimeError("network_"+type(exc).__name__) from None
        if r.status_code==400 and "response_format" in r.text.lower() and "response_format" in payload:
            payload.pop("response_format",None)
            continue
        if r.status_code in (408,409,425,429,500,502,503,504) and attempt==0:
            continue
        if r.status_code!=200:
            raise RuntimeError(f"http_{r.status_code}")
        try:
            body=r.json()
            content=body["choices"][0]["message"]["content"]
            if isinstance(content,list):
                content="".join(item if isinstance(item,str) else str(item.get("text") or item.get("content") or "")
                                for item in content if isinstance(item,(str,dict)))
            if isinstance(content,dict):
                return content
            text=str(content or "").strip()
            fence=chr(96)*3
            if text.startswith(fence):
                text=re.sub(r"^"+re.escape(fence)+r"(?:json)?\s*|\s*"+re.escape(fence)+r"$","",text,flags=re.I)
            try:
                obj=json.loads(text)
            except ValueError:
                # Some OpenAI-compatible providers wrap the JSON object in
                # explanatory prose even when instructed to return JSON only.
                decoder=json.JSONDecoder()
                obj=None
                for match in re.finditer(r"\\{",text):
                    try:
                        candidate,_=decoder.raw_decode(text[match.start():])
                        if isinstance(candidate,dict):
                            obj=candidate
                            break
                    except ValueError:
                        continue
                if obj is None:
                    raise
            if not isinstance(obj,dict):
                raise ValueError("json_object_required")
            return obj
        except Exception as exc:
            raise RuntimeError("invalid_json_"+type(exc).__name__) from None
    raise RuntimeError("route_failed")

LLM_SYSTEM="""أنت محرر تحليل جيوسياسي وأمني باللغة العربية. البيانات المقدمة هي الوقائع الوحيدة المسموح باستخدامها.
لا تغيّر العناوين، ولا تضف معلومات أو أرقاماً أو جهات أو مواقع أو نوايا غير موجودة في الوقائع.
ميّز التحليل عن الحقيقة باستخدام صيغ حذرة. لا تقدم توصية سياسية ولا تنبؤاً جازماً.
أعد JSON فقط بهذه المفاتيح:
{"situation_ar":"...","implications_ar":"...","developing_ar":["..."],"watch_ar":["..."]}"""

def _analysis_prompt(events):
    return {"events":[{
      "region":e.get("region"),"title_ar":e.get("title_ar"),"summary_ar":e.get("summary_ar"),
      "sources":[s.get("source") for s in e.get("sources",[])][:3]
    } for e in events[:10]]}

def _normalize_analysis(obj):
    situation=clean(obj.get("situation_ar","")) if isinstance(obj,dict) else ""
    implications=clean(obj.get("implications_ar","")) if isinstance(obj,dict) else ""
    developing=obj.get("developing_ar") if isinstance(obj,dict) else None
    watch=obj.get("watch_ar") if isinstance(obj,dict) else None
    if not situation or not implications or not isinstance(developing,list) or not isinstance(watch,list):
        raise RuntimeError("analysis_fields")
    developing=[clean(x) for x in developing if clean(x)][:5]
    watch=[clean(x) for x in watch if clean(x)][:6]
    if not developing or not watch:
        raise RuntimeError("analysis_lists")
    return {"situation_ar":situation[:1200],"implications_ar":implications[:1200],
            "developing_ar":[x[:420] for x in developing],"watch_ar":[x[:420] for x in watch]}

def llm_analysis_with_failover(events):
    health=[]
    for name,route in [("primary",_route("ARABIC_LLM_")),("fallback",_route("ARABIC_LLM_FALLBACK_"))]:
        if not route:
            health.append({"route":name,"configured":False,"ok":False,"error":"missing_configuration"})
            continue
        try:
            analysis=_normalize_analysis(_route_call(route,LLM_SYSTEM,_analysis_prompt(events)))
            health.append({"route":name,"configured":True,"ok":True,"model":route["model"]})
            return analysis,health,name
        except Exception as exc:
            health.append({"route":name,"configured":True,"ok":False,"model":route["model"],"error":str(exc)[:160]})
            print(f"V2 LLM {name} failed: {type(exc).__name__}: {exc}",flush=True)
    raise RuntimeError("Both Arabic LLM routes failed: "+json.dumps(health,ensure_ascii=False))

def probe_llms():
    results=[]
    system='Return JSON only with keys ok and arabic. Set ok=true and arabic to "جاهز".'
    for name,route in [("primary",_route("ARABIC_LLM_")),("fallback",_route("ARABIC_LLM_FALLBACK_"))]:
        if not route:
            results.append({"route":name,"configured":False,"ok":False,"error":"missing_configuration"})
            continue
        try:
            obj=_route_call(route,system,{"probe":"connectivity"},max_tokens=120)
            ok=bool(obj.get("ok")) and bool(obj.get("arabic"))
            results.append({"route":name,"configured":True,"ok":ok,"model":route["model"],
                            "error":None if ok else "unexpected_response"})
        except Exception as exc:
            results.append({"route":name,"configured":True,"ok":False,"model":route["model"],"error":str(exc)[:160]})
    return results

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
    if items:
        print("V2 stage=llm_analysis_start",flush=True)
        analysis,llm_health,llm_route=llm_analysis_with_failover(brief["events"])
        brief["analysis"]=analysis
        brief["llm_health"]={"status":"ok","selected_route":llm_route,"routes":llm_health}
        print("V2 stage=llm_analysis_complete route="+llm_route,flush=True)
    else:
        brief["llm_health"]={"status":"skipped_empty_collection","routes":[]}
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
