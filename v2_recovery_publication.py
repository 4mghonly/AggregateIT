"""Development-only bridge from existing V2 editorial plans to persistent weekly product."""
from __future__ import annotations
from html import escape
from v2_product_recovery import compact_sections

def ingest_editorial_plan(history,plan):
    if not isinstance(plan,dict) or plan.get("schema")!="aggregateit-editorial-plan/1":
        raise ValueError("invalid_editorial_plan")
    product=plan.get("product")
    if product not in ("english","arabic"):raise ValueError("invalid_product")
    day=plan["as_of"][:10]
    rows=[]
    for item in plan.get("items",[]):
        ev=item.get("evidence") or {}
        if not ev.get("quote") or not ev.get("source_url"):continue
        rows.append({"event_id":item["event_id"],"headline":ev["quote"][:300],
                     "summary":ev["quote"][:1000],"region":item["region"],
                     "priority":item["priority"],"topic":item.get("topic","geopolitics"),
                     "source_url":ev["source_url"]})
    return history.record("en" if product=="english" else "ar",day,rows)

def render_recovery_html(report):
    ar=report["language"]=="ar"
    direction="rtl" if ar else "ltr"
    title="المراجعة الأسبوعية للتطورات" if ar else "Weekly developments review"
    coverage=(f'{report["days_observed"]}/7 أيام رصد فعلية' if ar else f'{report["days_observed"]}/7 days observed')
    if not report["complete_week"]:
        coverage+=(" — سجل أسبوعي غير مكتمل" if ar else " — incomplete historical coverage")
    cards=[]
    for item in report["events"]:
        timeline="".join(
            '<li><time>'+escape(row["date"])+'</time> — '+escape(row["development"])+'</li>'
            for row in item["timeline"])
        links=" ".join('<a href="'+escape(url,quote=True)+'" rel="noopener noreferrer">'+
                       ("المصدر" if ar else "Source")+'</a>' for url in item["source_urls"])
        assessment=item.get("assessment",{}).get("ar" if ar else "en","")
        insight=("<p class=\"assessment\">"+escape(assessment)+"</p>") if assessment else ""
        cards.append('<article><h2>'+escape(item["headline"])+'</h2><p>'+
                     escape(item["region"])+' · '+str(item["observation_days"])+
                     (' أيام رصد' if ar else ' observed days')+'</p><ol>'+timeline+
                     '</ol>'+insight+'<p>'+links+'</p></article>')
    sections=compact_sections({"events":"".join(cards)})
    body=sections.get("events","")
    return ('<!doctype html><html lang="'+report["language"]+'" dir="'+direction+'"><head>'
            '<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            '<style>body{margin:0;background:#f3f1ec;color:#182d35;font:16px/1.65 system-ui,sans-serif}'
            'main{max-width:900px;margin:auto;padding:30px}article{background:white;border:1px solid #ddd;'
            'padding:24px;margin:16px 0;border-radius:8px}h1,h2{line-height:1.3}a{color:#176175}'
            'li{padding:5px 0}header{border-bottom:3px solid #b59b70}</style></head><body><main>'
            '<header><h1>'+title+'</h1><p>'+coverage+'</p></header>'+body+'</main></body></html>')
