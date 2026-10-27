"""B37: private mobile QA markup using actual source-linked RSS *headlines* only.

No original article body, editorial claim, LLM synthesis, or delivery is made.
Transport and browser orchestration are separate and explicitly no-post.
"""
from __future__ import annotations

from datetime import datetime
from html import escape
import re
from urllib.parse import urlsplit

ARABIC = re.compile(r'[\u0600-\u06ff\u0750-\u077f]')
LATIN = re.compile(r'[A-Za-z]')


def _safe_https(value: str) -> str:
    if not isinstance(value, str) or len(value)>2000:
        raise ValueError('invalid_source_link')
    p=urlsplit(value)
    if p.scheme!='https' or not p.hostname or p.username or p.password or p.port==0:
        raise ValueError('invalid_source_link')
    return value


def render_source_watch_html(product: str, candidates: list[dict], observed_at: str,
                             *, max_items: int = 6) -> dict:
    if product not in ('english','arabic') or not isinstance(candidates,list) or len(candidates)>2000:
        raise ValueError('invalid_source_watch_input')
    if type(max_items) is not int or not 1<=max_items<=8:
        raise ValueError('invalid_display_budget')
    try:
        stamp=datetime.fromisoformat(observed_at)
    except (TypeError,ValueError) as exc:
        raise ValueError('invalid_observation_time') from exc
    if stamp.utcoffset() is None:
        raise ValueError('observation_timezone_required')
    cards=[];filtered=0;overflow=0
    for item in candidates:
        if not isinstance(item,dict): raise ValueError('invalid_headline_candidate')
        title=item.get('title')
        if not isinstance(title,str) or not 5<=len(title)<=300:
            raise ValueError('invalid_headline')
        url=_safe_https(item.get('article_url'))
        source=_safe_https(item.get('source_feed_url'))
        observed=item.get('published_at')
        try:
            when=datetime.fromisoformat(observed)
            if when.utcoffset() is None: raise ValueError('naive')
        except (TypeError, ValueError) as exc:
            raise ValueError('invalid_publication_date') from exc
        if not (ARABIC.search(title) if product=='arabic' else LATIN.search(title)):
            filtered+=1;continue
        if len(cards)>=max_items:
            overflow+=1;continue
        cards.append('<article class="story"><div class="meta">'+escape(urlsplit(source).hostname or '')+' · '+escape(when.date().isoformat())+'</div><h2><a href="'+escape(url,quote=True)+'" rel="noopener noreferrer">'+escape(title)+'</a></h2></article>')
    ar=product=='arabic'
    lang='ar' if ar else 'en'; direction='rtl' if ar else 'ltr'
    heading='مراجعة عناوين المصادر' if ar else 'LIVE RSS HEADLINE WATCH'
    note=('عناوين من خلاصات المصدر فقط — ليست تحققاً من محتوى المقال' if ar else
          'Publisher feed headlines only — article facts not independently verified')
    sparse=('لا توجد عناوين متاحة وفق معايير العرض' if ar else 'No eligible source headlines in this capture')
    body=''.join(cards) if cards else '<p class="empty">'+sparse+'</p>'
    html=('<!doctype html><html lang="'+lang+'" dir="'+direction+'"><head><meta charset="utf-8">'
          '<meta name="viewport" content="width=device-width,initial-scale=1"><title>'+heading+'</title>'
          '<style>*{box-sizing:border-box}body{margin:0;background:#111d29;color:#f5f4ed;font-family:system-ui,sans-serif;line-height:1.5}'
          'main{max-width:950px;margin:auto;padding:clamp(16px,4vw,28px)}header{border-bottom:2px solid #bc9f6d}'
          'h1{font-size:clamp(26px,5vw,46px);line-height:1.2}h2{font-size:clamp(22px,4vw,34px);line-height:1.35;overflow-wrap:anywhere}'
          '.story{padding:16px 0;border-bottom:1px solid #496074}.meta,p{color:#bccbd2;overflow-wrap:anywhere;font-size:15px}'
          'a{color:#f5f4ed;text-decoration:underline;text-decoration-color:#bc9f6d;overflow-wrap:anywhere}'
          'article,main{min-width:0}footer{padding-top:18px}</style></head><body><main><header><h1>'+heading+'</h1><p>'+escape(note)+'</p></header>'
          +body+'<footer><p>'+escape(stamp.isoformat())+'</p></footer></main></body></html>')
    return {'schema':'aggregateit-v2-b37-live-headline-mobile/1','product':product,
            'html':html,'shown':len(cards),'script_filtered':filtered,
            'excluded_over_budget':overflow,'article_body_verified':False,
            'can_publish':False,'delivery_authorized':False,'discord_sent':False}
