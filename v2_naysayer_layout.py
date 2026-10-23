"""Offline standalone bilingual Naysayer HTML preview, never a live sender."""
from __future__ import annotations
from html import escape

TITLES={'english':('Critical assessment','Weekly challenge review','Insufficient evidence'),
        'arabic':('اختبار الفرضية','المراجعة النقدية الأسبوعية','الأدلة غير كافية')}

def render_review_html(report:dict)->str:
    if not isinstance(report,dict) or report.get('schema')!='aggregateit-naysayer-report/1' or report.get('delivery_authorized') is not False:
        raise ValueError('offline_review_contract_required')
    product=report.get('product');cadence=report.get('cadence')
    if product not in TITLES or cadence not in ('daily','weekly'):
        raise ValueError('unsupported_review_product')
    sections=report.get('sections')
    if not isinstance(sections,list) or not (len(sections)==1 if cadence=='daily' else 3<=len(sections)<=5):
        raise ValueError('invalid_review_layout_count')
    title=TITLES[product][0 if cadence=='daily' else 1]
    rtl=product=='arabic';lang='ar' if rtl else 'en';direction='rtl' if rtl else 'ltr'
    elements=[]
    for i,section in enumerate(sections):
        if not isinstance(section,dict) or not isinstance(section.get('review_status'),str):
            raise ValueError('invalid_review_layout_section')
        state=section['review_status']
        if state not in ('supported_challenge','assessment_survives','insufficient_evidence','withheld'):
            raise ValueError('invalid_review_status')
        if state in ('withheld','insufficient_evidence'):
            body=f'<p class="absence">{escape(TITLES[product][2])}</p>'
        else:
            lead=escape(str(section.get('lead_assessment','')))
            challenge=escape(str(section.get('challenge','')))
            if not lead.strip():raise ValueError('missing_lead_assessment')
            labels=('Assessment','Challenge','Evidence','Change since prior week') if not rtl else ('التقدير','الاعتراض','الأدلة','التغير منذ الأسبوع السابق')
            refs=section.get('cited_evidence',[])
            if not isinstance(refs,list) or not refs:raise ValueError('missing_review_citations')
            reftext=', '.join(escape(str(x.get('excerpt_id',''))) for x in refs if isinstance(x,dict))
            body=f'<p><strong>{labels[0]}:</strong> {lead}</p>'
            if challenge.strip():body+=f'<p><strong>{labels[1]}:</strong> {challenge}</p>'
            body+=f'<p class="refs"><strong>{labels[2]}:</strong> {reftext}</p>'
            if cadence=='weekly':
                change=escape(str(section.get('weekly_change','')))
                if not change.strip():raise ValueError('weekly_delta_missing')
                body+=f'<p><strong>{labels[3]}:</strong> {change}</p>'
        elements.append(f'<section class="challenge"><div class="number">{i+1:02d} / {escape(state.replace("_"," "))}</div>{body}</section>')
    css='''
:root{color-scheme:dark}*{box-sizing:border-box}body{margin:0;background:#111c23;color:#e7edf0;font:16px/1.58 system-ui,"Noto Sans Arabic",sans-serif}
main{max-width:1100px;margin:auto;padding:clamp(22px,5vw,68px)}
header{border-bottom:1px solid #5e7380;padding-bottom:22px;margin-bottom:30px}
.kicker{font-size:.76rem;letter-spacing:.13em;color:#a8b7b8;font-weight:700}.warn{font-size:.72rem;color:#edb98e}
h1{font-size:clamp(1.8rem,4vw,2.8rem);line-height:1.3;margin:.15em 0 .4em}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,390px),1fr));gap:18px}
.challenge{background:#1b2b32;border:1px solid #39505a;border-inline-start:4px solid #c6a778;padding:clamp(18px,3vw,30px);overflow-wrap:anywhere}
.challenge p{margin:.85em 0}.number{font-size:.72rem;color:#d7b891;text-transform:uppercase;letter-spacing:.08em}
.refs{font-size:.83rem;color:#b7c8ce}.absence{color:#dec7a2;font-style:italic}
footer{margin-top:32px;padding-top:14px;border-top:1px solid #4b5e65;color:#a9b7bd;font-size:.76rem}
@media(max-width:650px){body{font-size:17px}.grid{display:block}.challenge{margin-bottom:14px}}
@media print{body{background:white;color:#14252e}.challenge{background:white;color:#14252e;break-inside:avoid}.warn{color:#7e371c}}
'''
    return (f'<!doctype html><html lang="{lang}" dir="{direction}"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{escape(title)}</title><style>{css}</style></head><body><main>'
            f'<header><div class="kicker">AGGREGATEIT V2 / {escape(cadence.upper())}</div>'
            f'<h1>{escape(title)}</h1><div class="warn">SYNTHETIC / UNVERIFIED — NOT FOR DELIVERY</div></header>'
            f'<div class="grid">{"".join(elements)}</div>'
            '<footer>Evidence IDs are references, not proof of factual accuracy. No live publication.</footer>'
            '</main></body></html>')
