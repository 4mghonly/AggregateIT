"""Deterministic, evidence-linked English/Arabic weekly HTML preview; no sender."""
from __future__ import annotations

from html import escape
from math import isfinite
from urllib.parse import urlsplit

AR_REGIONS = {'gcc':'دول مجلس التعاون الخليجي','oman':'عُمان','iran':'إيران',
              'turkey':'تركيا','iraq':'العراق','yemen':'اليمن','egypt':'مصر',
              'sudan':'السودان','sahel':'الساحل','north_africa':'شمال أفريقيا',
              'pakistan':'باكستان','afghanistan':'أفغانستان','horn':'القرن الأفريقي',
              'somalia':'الصومال','levant':'بلاد الشام',
              'palestine_israel':'فلسطين وإسرائيل','jordan':'الأردن'}

def _safe_text(value, limit=240):
    if not isinstance(value, str) or not value or len(value)>limit:
        raise ValueError('invalid_weekly_display_string')
    return escape(value,quote=True)

def _safe_link(url):
    if not isinstance(url,str):
        raise ValueError('invalid_weekly_source_url')
    parts=urlsplit(url)
    if parts.scheme!='https' or not parts.hostname or parts.username or parts.password:
        raise ValueError('invalid_weekly_source_url')
    return escape(url,quote=True)

CSS = """
*{box-sizing:border-box}body{margin:0;background:#e9e6dd;color:#1a3036;font-family:Georgia,serif}
main{max-width:1160px;margin:auto;background:#faf8f3;padding:clamp(22px,5vw,58px)}
header{border-top:7px solid #183a49;border-bottom:1px solid #baa88c;padding:20px 0 26px}
.brand{font:700 .77rem Arial,sans-serif;color:#aa7643;letter-spacing:.17em}
h1{font-size:clamp(2rem,5vw,3.4rem);line-height:1.08;margin:.28em 0 .1em}
.subtitle{font:1rem/1.5 Arial,sans-serif;color:#677477}
.warning{font:700 .73rem Arial,sans-serif;color:#a44b37;letter-spacing:.06em;margin-top:10px}
.metrics{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin:23px 0}
.metric{background:#ede9e0;border-inline-start:3px solid #b89769;padding:17px;font:700 .75rem Arial,sans-serif}
.metric strong{display:block;font:700 1.65rem Georgia,serif;color:#1b4551;margin-top:4px}
.columns{display:grid;grid-template-columns:1.6fr 1fr;gap:17px}.panel{background:#fffdf8;border:1px solid #d3c6b5;padding:24px;min-width:0;margin-bottom:18px}
h2{font-size:1.25rem;margin:0 0 18px;padding-bottom:10px;border-bottom:1px solid #cfc1ab}
h3{overflow-wrap:anywhere;font-size:1.03rem;margin:9px 0}
.story{padding:17px 0;border-bottom:1px solid #e6ddd2}.story:last-child{border-bottom:0}
.eyebrow{font:700 .72rem Arial,sans-serif;color:#95683e;letter-spacing:.04em}
.small{font:.83rem/1.55 Arial,sans-serif;color:#5f6c71;overflow-wrap:anywhere}
a{font:700 .83rem Arial,sans-serif;color:#176172;text-decoration-thickness:1px;text-underline-offset:4px}
.scroller{overflow-x:auto}table{border-collapse:collapse;width:100%;font:.85rem Arial,sans-serif}
th,td{text-align:start;padding:12px 8px;border-bottom:1px solid #ddd3c7;white-space:nowrap}
footer{border-top:1px solid #c5b598;margin-top:22px;padding-top:16px;color:#647279;font:.8rem/1.5 Arial,sans-serif}
@media(max-width:740px){main{padding:18px}.metrics,.columns{display:block}.metric{margin:8px 0}}
@media print{body{background:white}main{padding:12mm}.story{break-inside:avoid}}
body[dir=rtl]{background:#0d1a24;color:#ecf0f0;font-family:Tahoma,'Noto Sans Arabic',Arial,sans-serif}
body[dir=rtl] main{background:#162736}body[dir=rtl] header{border-top-color:#c2a16e;border-bottom-color:#607681}
body[dir=rtl] .panel,body[dir=rtl] .metric{background:#233b49;border-color:#536b77}
body[dir=rtl] .metric strong{color:#f4d69f}
body[dir=rtl] h2,body[dir=rtl] .story{border-bottom-color:#526a76}
body[dir=rtl] .small,body[dir=rtl] .subtitle,body[dir=rtl] footer{color:#cbd5d8}
body[dir=rtl] .eyebrow,body[dir=rtl] .brand{color:#e7be88}
body[dir=rtl] .warning{color:#ffc0a0}body[dir=rtl] a{color:#d4e0e2}
"""

def render_weekly_html(report:dict)->str:
    if (not isinstance(report,dict) or report.get('schema')!='aggregateit-v2-weekly-rollup/1'
            or report.get('delivery_authorized') is not False or report.get('window_days')!=7):
        raise ValueError('weekly_rollup_contract_required')
    product=report.get('product')
    if product not in ('english','arabic'):raise ValueError('unknown_weekly_product')
    rtl=product=='arabic'
    markets=report.get('market_changes',[])
    if not isinstance(markets,list) or len(markets)>50:raise ValueError('invalid_market_series')
    if rtl and markets:raise ValueError('arabic_weekly_finance_forbidden')
    stories=report.get('stories')
    if not isinstance(stories,list) or len(stories)>50:raise ValueError('invalid_weekly_stories')
    story_html=[]
    statuses={'updated_during_week':('Changed during the week','تطور خلال الأسبوع'),
              'new_with_verified_baseline':('New against recorded baseline','جديد مقارنة بالمرجع'),
              'observed_no_verified_baseline':('Observed; baseline unverified','رُصد دون مرجع مؤكد')}
    for i,item in enumerate(stories,1):
        if not isinstance(item,dict):raise ValueError('invalid_weekly_story')
        evidence=item.get('evidence')
        if not isinstance(evidence,dict):raise ValueError('missing_weekly_evidence')
        event=_safe_text(item.get('event_id'),400)
        # Prefer the original bounded source excerpt over a cryptic event ID.
        visible_headline=_safe_text(evidence['quote'],240) if evidence.get('quote') else event
        excerpt=_safe_text(evidence.get('excerpt_id'))
        source=_safe_text(evidence.get('source_id'))
        link=_safe_link(evidence.get('source_url'))
        change=item.get('change_status')
        if change not in statuses:raise ValueError('invalid_weekly_change_status')
        region=item.get('region')
        region=_safe_text(AR_REGIONS.get(region,region) if rtl else region.upper().replace('_',' '))
        title=statuses[change][1 if rtl else 0]
        label=('مرجع المقتطف' if rtl else 'Exact excerpt')
        story_html.append(f'<article class="story"><div class="eyebrow">{i:02d} · {region} · {title}</div>'
                          f'<h3>{visible_headline}</h3><p class="small">{label}: {excerpt} · {source}</p>'
                          f'<a href="{link}" rel="noopener noreferrer" target="_blank">'
                          f'{"عرض المقال الأصلي" if rtl else "Open source document"} ↗</a></article>')
    market_lines=[]
    for item in markets:
        if not isinstance(item,dict):raise ValueError('invalid_market_series')
        before,after,pct=item.get('first_value'),item.get('last_value'),item.get('change_pct')
        if any(not isinstance(v,(float,int)) or isinstance(v,bool) or not isfinite(v) for v in (before,after)):
            raise ValueError('invalid_market_series')
        if pct is not None and (not isinstance(pct,(float,int)) or isinstance(pct,bool) or not isfinite(pct)):
            raise ValueError('invalid_market_series')
        market_lines.append(f'<tr><th scope="row">{_safe_text(item.get("instrument"))}</th>'
                            f'<td>{before:g} → {after:g} {_safe_text(item.get("unit"),80)}</td>'
                            f'<td>{f"{pct:+.3f}%" if pct is not None else "—"}</td>'
                            f'<td>{_safe_text(item.get("source"))}</td></tr>')
    uncovered=report.get('regions_uncovered',[])
    if not isinstance(uncovered,list) or len(uncovered)>30:raise ValueError('invalid_weekly_coverage')
    gaps=', '.join(_safe_text(AR_REGIONS.get(r,r) if rtl else r.upper().replace('_',' ')) for r in uncovered)
    if not gaps:gaps='لا توجد فجوات مسجلة' if rtl else 'No gaps recorded'
    for count in ('unique_events','days_with_snapshots'):
        if type(report.get(count)) is not int or report[count]<0:raise ValueError('invalid_weekly_counts')
    labels=({'brand':'نشرة المتابعة الاستراتيجية','edition':'التقرير الأسبوعي',
              'sub':'التطورات الجيوسياسية والأمنية',
              'events':'الأحداث المرصودة','days':'أيام الرصد','gaps':'الفجوات الجغرافية',
              'stories':'سجل التطورات','critical':'اختبار الفرضيات',
              'abstain':'الأدلة غير كافية لمراجعة نقدية موثقة',
              'analysis':'التحليل الاستراتيجي مؤجل بانتظار التحقق المستقل'}
            if rtl else
            {'brand':'AGGREGATEIT','edition':'Weekly Intelligence Review',
             'sub':'Geopolitics & Financial Markets','events':'Unique developments',
             'days':'Days observed','gaps':'Geographic coverage gaps',
             'stories':'Source-bound event evolution','critical':'Critical desk',
             'abstain':'Evidence insufficient for a critical review',
             'analysis':'Deeper analysis withheld pending independent editorial validation'})
    market_section='' if rtl else (
        '<section class="panel"><h2>Market performance</h2>'
        '<p class="small">Dated observations only; no inferred prices.</p>'
        '<div class="scroller"><table><thead><tr><th>Instrument</th><th>Observed window</th>'
        '<th>Change</th><th>Source</th></tr></thead><tbody>'
        + (''.join(market_lines) if market_lines else '<tr><td colspan="4">No comparable market observations</td></tr>')
        + '</tbody></table></div></section>')
    language='ar' if rtl else 'en';direction='rtl' if rtl else 'ltr'
    return (f'<!doctype html><html lang="{language}" dir="{direction}"><head>'
            f'<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{labels["edition"]}</title><style>{CSS}</style></head>'
            f'<body dir="{direction}"><main><header><div class="brand">{labels["brand"]}</div>'
            f'<h1>{labels["edition"]}</h1><div class="subtitle">{labels["sub"]}</div>'
            f'<div class="warning">SYNTHETIC / UNVERIFIED — NOT FOR DELIVERY</div></header>'
            f'<div class="metrics"><div class="metric">{labels["events"]}<strong>{report["unique_events"]}</strong></div>'
            f'<div class="metric">{labels["days"]}<strong>{report["days_with_snapshots"]}</strong></div>'
            f'<div class="metric">{labels["gaps"]}<strong>{len(uncovered)}</strong></div></div>'
            f'<div class="columns"><section class="panel"><h2>{labels["stories"]}</h2>'
            f'{"".join(story_html) if story_html else "<p>No admitted observations</p>"}</section>'
            f'<aside><section class="panel"><h2>{labels["critical"]}</h2>'
            f'<p>{labels["abstain"]}</p></section><section class="panel"><h2>{labels["gaps"]}</h2>'
            f'<p>{gaps}</p></section><section class="panel"><h2>{labels["edition"]}</h2>'
            f'<p>{labels["analysis"]}</p></section></aside></div>{market_section}'
            f'<footer>Evidence IDs support navigation, not verified factual accuracy. No live publication.</footer>'
            f'</main></body></html>')
