"""Evidence-only HTML visual proof for externally observed excerpts.

This is not the final Gazette renderer. It is a no-post inspector of authentic,
partial web-text handoffs to B3/B4. Never synthesizes event descriptions.
"""
from __future__ import annotations

from html import escape
from urllib.parse import urlsplit

from v2_feed_probe import _url_safe

CSS = r"""
*{box-sizing:border-box}
:root{--ink:#21343a;--muted:#677982;--accent:#a77c4e;--border:#d6cbc0}
body{margin:0;background:#e4e0d7;color:var(--ink);font-family:Georgia,'Times New Roman',serif}
.sheet{max-width:1600px;min-height:900px;background:#f8f5ef;margin:0 auto;padding:68px 76px}
.masthead{border-top:8px solid #214651;border-bottom:2px solid #a77c4e;padding:25px 0 32px}
.eyebrow{font:bold 17px/1.3 Arial,sans-serif;text-transform:uppercase;letter-spacing:.18em;color:var(--accent)}
h1{font-size:55px;line-height:1.05;margin:15px 0 7px;letter-spacing:-.035em}
.subtitle{font:22px/1.5 Arial,sans-serif;color:var(--muted)}
.status{font:bold 15px/1.3 Arial,sans-serif;color:#a04436;letter-spacing:.12em;margin-top:20px}
.summary{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:18px;margin:32px 0}
.metric{background:#eae5da;padding:24px;border-top:3px solid var(--accent)}
.metric strong{display:block;font:700 40px Georgia,serif;margin-top:8px}
.metric span{font:700 15px/1.4 Arial,sans-serif;color:var(--muted);letter-spacing:.04em}
.columns{display:grid;grid-template-columns:minmax(0,1.8fr) minmax(280px,1fr);gap:24px}
.panel{background:white;border:1px solid var(--border);padding:30px;margin:0 0 24px;min-width:0}
h2{font:700 23px Georgia,serif;margin:0 0 19px;border-bottom:1px solid var(--border);padding-bottom:13px}
.story{padding:18px 0;border-top:1px solid #eee6df}.story:first-of-type{border-top:0;padding-top:0}
.source{font:700 14px/1.35 Arial,sans-serif;color:var(--accent);text-transform:uppercase;letter-spacing:.08em}
.quote{font:25px/1.65 Georgia,serif;margin:12px 0 16px;overflow-wrap:anywhere}
.meta{font:15px/1.5 Arial,sans-serif;color:var(--muted);overflow-wrap:anywhere}
a{color:#196172;font:700 16px Arial,sans-serif;text-underline-offset:3px}
.small{font:18px/1.6 Arial,sans-serif;color:var(--muted);margin:11px 0}
.footer{margin-top:22px;border-top:1px solid var(--border);padding-top:20px;font:15px/1.5 Arial,sans-serif;color:var(--muted)}
body[dir=rtl]{background:#0c1922;color:#e7edf0;font-family:Tahoma,'Noto Naskh Arabic','Noto Sans Arabic',Arial,sans-serif;--ink:#e7edf0;--muted:#c5d2d7;--border:#516878;--accent:#e2bd80}
body[dir=rtl] .sheet{background:#142a39}
body[dir=rtl] .masthead{border-top-color:#d7b47c;border-bottom-color:#567384}
body[dir=rtl] .panel,body[dir=rtl] .metric{background:#1e3848}
body[dir=rtl] .quote{font:28px/1.95 Tahoma,'Noto Naskh Arabic',Arial,sans-serif}
body[dir=rtl] a{color:#a9d1dc}
body[dir=rtl] .status{color:#ffbb99}
body[dir=rtl] .story{border-top-color:#425b67}
@media(max-width:900px){.sheet{padding:32px 25px}.summary{gap:8px}.columns{display:block}h1{font-size:36px}.quote{font-size:21px}.metric{padding:15px}.metric strong{font-size:27px}}
@media print{body{background:white!important}.sheet{min-height:0;padding:20px}.panel,.story{break-inside:avoid}}
"""

_REGIONS={'gcc':'دول الخليج','yemen':'اليمن','sudan':'السودان','oman':'عُمان',
          'iraq':'العراق','iran':'إيران','jordan':'الأردن','egypt':'مصر',
          'palestine_israel':'فلسطين وإسرائيل','somalia':'الصومال',
          'horn':'القرن الأفريقي','sahel':'الساحل','pakistan':'باكستان',
          'afghanistan':'أفغانستان','north_africa':'شمال أفريقيا','turkey':'تركيا',
          'levant':'بلاد الشام'}


def render_capture_preview(report: dict, *, product: str) -> str:
    if (not isinstance(report, dict) or
            report.get('schema') != 'aggregateit-v2-external-capture-rehearsal/1' or
            report.get('source_provenance_status') != 'web_text_excerpt_observed_not_independently_verified' or
            report.get('delivery_authorized') is not False or
            report.get('web_collector_ran') is not False or report.get('llm_called') is not False):
        raise ValueError('untrusted_capture_preview')
    if product not in ('english','arabic'):
        raise ValueError('unknown_product')
    item=report.get('products',{}).get(product)
    if not isinstance(item,dict) or item.get('delivery_authorized') is not False:
        raise ValueError('untrusted_product_candidate')
    stories=item.get('stories')
    if not isinstance(stories,list) or len(stories)>20:
        raise ValueError('invalid_story_count')
    ar=product=='arabic'
    stories_html=[]
    for story in stories:
        if not isinstance(story,dict) or story.get('verification')!='publisher_attributed_unverified':
            raise ValueError('story_not_attributed_as_unverified')
        uri=_url_safe(story.get('source_url'))
        region=story.get('region')
        if not isinstance(region,str) or not region:
            raise ValueError('invalid_story_region')
        sid=story.get('source_id');excerpt=story.get('excerpt_id')
        quote=story.get('quote')
        if any(not isinstance(v,str) or not v or len(v)>240 for v in (sid,excerpt,quote)):
            raise ValueError('invalid_source_quote')
        title=_REGIONS.get(region,region) if ar else region.upper().replace('_',' ')
        stories_html.append(
            f'<article class="story"><div class="source">{escape(title)} · {escape(sid)}</div>'
            f'<p class="quote">{escape(quote)}</p><div class="meta">'
            f'{"معرّف المقتطف" if ar else "Excerpt ID"}: {escape(excerpt)}</div>'
            f'<p><a href="{escape(uri,quote=True)}" rel="noopener noreferrer" target="_blank">'
            f'{"المصدر الأصلي" if ar else "Read original source"} ↗</a></p></article>')
    gaps=item.get('coverage_gaps') or []
    if not isinstance(gaps,list):raise ValueError('invalid_coverage_gaps')
    gap_text='، '.join(escape(_REGIONS.get(g,g)) for g in gaps[:6]) if ar else ', '.join(escape(g.replace('_',' ')) for g in gaps[:6])
    if len(gaps)>6:gap_text+=f' … +{len(gaps)-6}'
    if not gap_text:gap_text='لا توجد فجوات مسجلة في العينة' if ar else 'No recorded gaps for this sample'
    names=({'title':'مكتب الأدلة | مقتطفات مرصودة','sub':'إحاطة عربية تجريبية — أمن وجغرافيا سياسية',
            'sources':'مقتطفات المصادر','gaps':'فجوات التغطية','count':'المقتطفات المختارة',
            'region':'مناطق ممثلة','history':'الأدلة المشتركة','note':'ليست نشرة قابلة للنشر',
            'limit':'نصوص جزئية نقلت من صفحات مرئية، دون التحقق من كامل المقال أو الترخيص أو استقلالية الجهات.',
            'market':'لا توجد بيانات أسواق في التقرير العربي.',
            'status':'غير متحقق · دون نموذج · دون نشر',
            'footer':'لم يتم تشغيل جامع مصادر حي أو نموذج آلي. لم يُصرَّح بالنشر.'}
           if ar else
           {'title':'Evidence Desk | Observed Excerpts','sub':'English source provenance — geopolitical observation sample',
            'sources':'Source excerpts','gaps':'Coverage gaps','count':'Admitted excerpts',
            'region':'Represented regions','history':'Evidence references','note':'NOT A PUBLISHABLE EDITION',
            'limit':'Partial public-web text only. No complete article, rights review, or independent publisher verification.',
            'market':'Market observations unavailable; no values inferred.',
            'status':'UNVERIFIED · NO MODEL · NO DISCORD',
            'footer':'No live feed collector or automated model was run. No publication authorized.'})
    distinct_regions={s['region'] for s in stories}
    lang='ar' if ar else 'en';dir_='rtl' if ar else 'ltr'
    article_html=''.join(stories_html) or '<p>No admissible observations</p>'
    return (f'<!doctype html><html lang="{lang}" dir="{dir_}"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{names["title"]}</title><style>{CSS}</style></head><body dir="{dir_}">'
            f'<main class="sheet"><header class="masthead"><div class="eyebrow">AGGREGATEIT · V2 RESEARCH LAB</div>'
            f'<h1>{names["title"]}</h1><div class="subtitle">{names["sub"]}</div>'
            f'<div class="status">{names["status"]}</div></header>'
            f'<div class="summary"><div class="metric"><span>{names["count"]}</span><strong>{len(stories)}</strong></div>'
            f'<div class="metric"><span>{names["region"]}</span><strong>{len(distinct_regions)}</strong></div>'
            f'<div class="metric"><span>{names["gaps"]}</span><strong>{len(gaps)}</strong></div></div>'
            f'<div class="columns"><section class="panel"><h2>{names["sources"]}</h2>{article_html}</section>'
            f'<aside><section class="panel"><h2>{names["note"]}</h2><p class="small">{names["limit"]}</p></section>'
            f'<section class="panel"><h2>{names["gaps"]}</h2><p class="small">{gap_text}</p></section>'
            f'<section class="panel"><h2>{names["history"]}</h2><p class="small">{names["market"]}</p>'
            f'</section></aside></div><footer class="footer">'
            f'{names["footer"]}</footer></main></body></html>')
