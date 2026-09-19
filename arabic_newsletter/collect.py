"""Bounded collection and publisher-linked social discovery. Never invent feed success."""
import calendar
import json
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from urllib.parse import urljoin, urlsplit
import feedparser
import requests
from bs4 import BeautifulSoup
from .core import ROOT, canonical, clean, digest, preliminary_relevant, uae_secondary_relevant, write_json

HEADERS={'User-Agent':'AggregateIT-Arabic/1.0 (public news briefing; RSS reader)'}
SOCIAL_HOSTS={'t.me':'telegram','twitter.com':'x','x.com':'x','youtube.com':'youtube','www.youtube.com':'youtube',
               'facebook.com':'facebook','www.facebook.com':'facebook','bsky.app':'bluesky'}

class FetchError(RuntimeError): pass

def fetch(url):
    if urlsplit(url).scheme not in ('https','http'): raise FetchError('unsupported_scheme')
    try:
        with requests.get(url, headers=HEADERS, timeout=(20,20), stream=True) as r:
            if r.status_code != 200: raise FetchError(f'http_{r.status_code}')
            chunks=[]; size=0
            for chunk in r.iter_content(65536):
                size+=len(chunk)
                if size>3_000_000: raise FetchError('response_too_large')
                chunks.append(chunk)
            return b''.join(chunks)
    except requests.RequestException:
        raise FetchError('network_error') from None

def text_html(value):
    return clean(BeautifulSoup(value or '', 'html.parser').get_text(' '))

def entry_time(entry):
    # Publication date, never retrieval date or an old story's modification date.
    stamp=entry.get('published_parsed') or entry.get('created_parsed')
    if stamp: return calendar.timegm(stamp)
    return None

def source_item(source, title, text, url, published, kind='news'):
    url=canonical(url)
    if urlsplit(url).scheme not in ('https','http'): return None
    return dict(id=digest(url)[:16],source_id=source['id'],source=source['name'],
      region=source['region'],country=source['country'],language=source['language'],
      affiliation=source['affiliation'],title=clean(title),text=clean(text)[:3500],url=url,
      published=published,retrieved=time.time(),kind=kind)

def social_links(soup, website):
    found={}
    for a in soup.select('a[href]'):
        url=urljoin(website,a['href']); p=urlsplit(url); host=p.hostname or ''
        platform=SOCIAL_HOSTS.get(host)
        if not platform or re.search(r'/(share|sharer|intent|watch)([/.?]|$)',p.path): continue
        if len(p.path.strip('/'))<2: continue
        key=canonical(url)
        found[key]={'platform':platform,'url':key,'verified_via':website,
          'status':'publisher_linked','collection':'supported' if platform=='telegram' else 'discovery_only'}
    return list(found.values())[:16]

def telegram(source, url):
    p=urlsplit(url); handle=p.path.strip('/').split('/')[0]
    if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]{4,}',handle): return []
    soup=BeautifulSoup(fetch('https://t.me/s/'+handle),'html.parser'); out=[]
    for post in soup.select('.tgme_widget_message')[-12:]:
        body=post.select_one('.tgme_widget_message_text'); date=post.select_one('time[datetime]')
        link=post.select_one('a.tgme_widget_message_date[href]')
        if not(body and date and link): continue
        try: ts=datetime.fromisoformat(date['datetime'].replace('Z','+00:00')).timestamp()
        except ValueError: continue
        text=body.get_text(' ',strip=True)
        out.append(source_item(source,text[:220],text,link['href'],ts,'social'))
    return [x for x in out if x]

def iso_time(value):
    try:
        date=datetime.fromisoformat(str(value).replace('Z','+00:00'))
        return date.timestamp() if date.tzinfo else None
    except (ValueError,TypeError): return None

def article_page(source,url):
    soup=BeautifulSoup(fetch(url),'html.parser')
    title=soup.select_one('meta[property="og:title"]')
    title=title.get('content','') if title else (soup.h1.get_text(' ',strip=True) if soup.h1 else '')
    published=None
    for selector in ('meta[property="article:published_time"]','meta[name="datePublished"]','meta[name="pubdate"]'):
        tag=soup.select_one(selector)
        if tag: published=iso_time(tag.get('content')); break
    def walk(value):
        if isinstance(value,dict):
            if value.get('datePublished'): yield value
            for v in value.values(): yield from walk(v)
        elif isinstance(value,list):
            for v in value: yield from walk(v)
    body=''
    for script in soup.select('script[type="application/ld+json"]'):
        try:
            for obj in walk(json.loads(script.string or script.get_text())):
                published=published or iso_time(obj.get('datePublished'))
                title=title or obj.get('headline','')
                body=body or obj.get('articleBody','')
        except (ValueError,TypeError): pass
    if not published or not title: return None
    article=soup.select_one('article') or soup.select_one('main')
    if not body and article: body=' '.join(p.get_text(' ',strip=True) for p in article.select('p'))
    if not body:
        tag=soup.select_one('meta[property="og:description"]')
        body=tag.get('content','') if tag else ''
    return source_item(source,title,body,url,published)

def webpage_items(source,soup):
    links={}; host=urlsplit(source['website']).hostname
    for a in soup.select('a[href]'):
        title=clean(a.get_text(' ',strip=True)); url=urljoin(source['website'],a['href']); p=urlsplit(url)
        if p.hostname!=host or p.scheme not in ('http','https') or len(title)<25 or len(title)>250: continue
        if not re.search(r'/[^/]+/[^/]+|[0-9]{3,}',p.path): continue
        if not preliminary_relevant(title,source['language']): continue
        links.setdefault(canonical(url),title)
    out=[]
    for url in list(links)[:3]:
        try:
            item=article_page(source,url)
            if item: out.append(item)
        except FetchError: pass
    return out

def youtube(source,url):
    p=urlsplit(url)
    match=re.fullmatch(r'/channel/(UC[A-Za-z0-9_-]{22})',p.path)
    if not match: return []  # Never guess channel IDs from handles or display names.
    parsed=feedparser.parse(fetch('https://www.youtube.com/feeds/videos.xml?channel_id='+match[1]))
    out=[]
    for e in parsed.entries[:10]:
        description=e.get('media_description') or e.get('summary','')
        item=source_item(source,e.get('title',''),text_html(description),e.get('link',''),entry_time(e),'social')
        if item: out.append(item)
    return out

def collect_source(source, discover=False):
    result={'id':source['id'],'name':source['name'],'region':source['region'],'country':source['country'],
       'checked_at':datetime.now(timezone.utc).isoformat(),'status':'failed','items':0,'social':[],'errors':[]}
    items=[]; soup=None; feeds=[source['feed']] if source.get('feed') else []
    if discover or not feeds:
        try:
            soup=BeautifulSoup(fetch(source['website']),'html.parser')
            for link in soup.select('link[type="application/rss+xml"],link[type="application/atom+xml"]'):
                if link.get('href'): feeds.append(urljoin(source['website'],link['href']))
            result['social']=social_links(soup,source['website'])
        except FetchError as e: result['errors'].append('website:'+str(e))
    for url in list(dict.fromkeys(feeds))[:2]:
        try:
            parsed=feedparser.parse(fetch(url))
            if not parsed.entries: raise FetchError('no_parseable_entries')
            result['feed']=url; result['status']='active'
            for e in parsed.entries[:35]:
                summary=e.get('summary','')
                if e.get('content'): summary=e['content'][0].get('value',summary)
                item=source_item(source,e.get('title',''),text_html(summary),e.get('link',''),entry_time(e))
                if item: items.append(item)
            break
        except FetchError as e: result['errors'].append('feed:'+str(e))
    if not feeds: result['errors'].append('no_discovered_feed')
    if not items:
        if soup is None:
            try: soup=BeautifulSoup(fetch(source['website']),'html.parser')
            except FetchError: pass
        if soup is not None:
            items.extend(webpage_items(source,soup))
            if items: result['status']='active'; result['method']='article_pages'
            if not result['social']: result['social']=social_links(soup,source['website'])
    # Only channels linked by this publisher, or preserved in an audited registry.
    socials=result['social'] or source.get('social',[])
    approved={s['url'] for s in source.get('social',[]) if s.get('approved')}
    for channel in socials:
        channel['approved']=channel['url'] in approved
    for channel in [s for s in socials if s.get('platform') in ('telegram','youtube') and s.get('verified_via')==source['website'] and s.get('approved')][:2]:
        try:
            social_items=(telegram if channel['platform']=='telegram' else youtube)(source,channel['url']); items.extend(social_items)
            channel['collection_status']='active' if social_items else 'empty'
        except FetchError as e: channel['collection_status']=str(e)
    result['social']=socials; result['items']=len(items)
    result['dated_items']=sum(bool(x['published']) for x in items)
    if items and result['status']!='active': result['status']='social_only'
    return items,result

def collect(start,end,discover=False,registry=None):
    sources=registry or json.loads((ROOT/'sources.json').read_text())
    items=[]; health=[]
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures={pool.submit(collect_source,s,discover):s for s in sources if s.get('enabled',True)}
        for future in as_completed(futures):
            source=futures[future]
            try: found,report=future.result()
            except Exception as e:
                found=[]; report={'id':source['id'],'name':source['name'],'region':source['region'],
                  'country':source['country'],'status':'failed','items':0,'errors':[type(e).__name__],'social':[]}
            items.extend(found); health.append(report)
    seen=set(); selected=[]
    for item in sorted(items,key=lambda x:x['published'] or 0,reverse=True):
        if not item['published'] or not start.timestamp() <= item['published'] < end.timestamp(): continue
        material=item['title']+' '+item['text']
        if not preliminary_relevant(material,item['language']):
            if item.get('country')!='AE' or not uae_secondary_relevant(material): continue
        key=digest(clean(item['title']).casefold())
        if item['id'] in seen or key in seen: continue
        seen.update([item['id'],key]); selected.append(item)
    # Round robin by region, then publisher; a prolific wire cannot consume the entire budget.
    buckets={}
    for item in selected: buckets.setdefault(item['region'],{}).setdefault(item['source_id'],[]).append(item)
    balanced=[]
    while buckets and len(balanced)<112:
        for region in list(buckets):
            publishers=buckets[region]
            sid=next(iter(publishers)); group=publishers.pop(sid)
            balanced.append(group.pop(0))
            if group: publishers[sid]=group
            if not publishers: del buckets[region]
            if len(balanced)>=112: break
    return balanced,sorted(health,key=lambda x:x['id'])

def audit(output):
    sources=json.loads((ROOT/'sources.json').read_text()); reports=[]; discovered=[]
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures={pool.submit(collect_source,s,True):s for s in sources if s.get('enabled',True)}
        for f in as_completed(futures):
            s=futures[f]
            try: _,report=f.result()
            except Exception as e: report={'id':s['id'],'status':'failed','errors':[type(e).__name__],'social':[]}
            reports.append(report)
            updated=dict(s)
            if report.get('feed'): updated['feed']=report['feed']
            updated['social']=report.get('social',[])
            updated['verification_status']=report['status']
            updated['verified_at']=report.get('checked_at')
            discovered.append(updated)
            print(s['id'],s['name'],report['status'],report.get('items',0),flush=True)
    output.mkdir(parents=True,exist_ok=True)
    write_json(output/'source_audit.json',sorted(reports,key=lambda r:r['id']))
    write_json(output/'discovered_sources.json',sorted(discovered,key=lambda r:r['id']))
