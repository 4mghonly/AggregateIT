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
from .core import ROOT, REGIONS, canonical, clean, digest, preliminary_relevant, uae_secondary_relevant, write_json

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
    # Prefer explicit publication/creation time. Atom commonly exposes only
    # updated_parsed, which is still publisher-supplied time and is safer than
    # substituting retrieval time. Strict edition-window filtering still applies.
    stamp=entry.get('published_parsed') or entry.get('created_parsed') or entry.get('updated_parsed')
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

def source_relevant(source,text):
    if preliminary_relevant(text,source.get('language','en')): return True
    return source.get('country')=='AE' and uae_secondary_relevant(text)

def article_path_candidate(path):
    parts=[part for part in path.strip('/').split('/') if part]
    if len(parts)>=2 or re.search(r'[0-9]{3,}',path): return True
    if len(parts)==1:
        slug=parts[0]
        return len(slug)>=24 and slug.count('-')>=3
    return False

def webpage_items(source,soup):
    links={}; host=urlsplit(source['website']).hostname
    for a in soup.select('a[href]'):
        title=clean(a.get_text(' ',strip=True)); url=urljoin(source['website'],a['href']); p=urlsplit(url)
        if p.hostname!=host or p.scheme not in ('http','https') or len(title)<25 or len(title)>250: continue
        if not article_path_candidate(p.path): continue
        key=canonical(url)
        # Headline relevance is a priority signal, not a hard gate. Foreign-language
        # and terse headlines often reveal their security relevance only in body text.
        links.setdefault(key,(title,0 if source_relevant(source,title) else 1))
    out=[]
    ordered=sorted(links.items(),key=lambda row:row[1][1])[:6]
    for url,_meta in ordered:
        try:
            item=article_page(source,url)
            if item and source_relevant(source,item['title']+' '+item['text']): out.append(item)
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
       'language':source.get('language','unknown'),'checked_at':datetime.now(timezone.utc).isoformat(),
       'status':'failed','items':0,'social':[],'errors':[]}
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

def production_sources(sources,end,non_arab_retry=18,arab_retry=6):
    """Keep healthy sources live and rotate failed-audit sources back through collection."""
    always=[s for s in sources if s.get('enabled',True) or s.get('verification_status')=='active']
    retry=[s for s in sources if s not in always and str(s.get('retired_reason','')).startswith('failed_source_audit_')]
    cycle=int(end.timestamp()//21600)
    def rotate(rows,count,salt):
        if not rows or count<=0: return []
        rows=sorted(rows,key=lambda x:x.get('id',''))
        start=(cycle*salt) % len(rows)
        ordered=rows[start:]+rows[:start]
        return ordered[:min(count,len(ordered))]
    non_arab=[s for s in retry if s.get('language')!='ar']
    arab=[s for s in retry if s.get('language')=='ar']
    chosen=always+rotate(non_arab,non_arab_retry,7)+rotate(arab,arab_retry,5)
    return list({s['id']:s for s in chosen}.values())

def _run_source_batch(sources,discover=False):
    """Collect a bounded source batch and return items plus health reports."""
    items=[]; health=[]
    if not sources: return items,health
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures={pool.submit(collect_source,s,discover):s for s in sources}
        for future in as_completed(futures):
            source=futures[future]
            try:
                found,report=future.result()
            except Exception as e:
                found=[]; report={'id':source['id'],'name':source['name'],'region':source['region'],
                  'country':source['country'],'language':source.get('language','unknown'),
                  'status':'failed','items':0,'errors':[type(e).__name__],'social':[]}
            items.extend(found); health.append(report)
    return items,health

def _same_region_substitutes(all_sources,attempted,weak_regions,max_per_region=6):
    """Choose alternate publishers from the same region when live coverage is weak."""
    attempted=set(attempted); chosen=[]
    for region in weak_regions:
        candidates=[s for s in all_sources if s.get('region')==region and s.get('id') not in attempted]
        # Prefer previously healthy/active publishers, then enabled sources, then
        # retired audit failures as recovery candidates. Mix languages where possible.
        candidates.sort(key=lambda s:(
            0 if s.get('verification_status')=='active' else 1,
            0 if s.get('enabled',True) else 1,
            str(s.get('language','')),
            str(s.get('id',''))
        ))
        languages=set(); selected=[]
        for s in candidates:
            lang=s.get('language','unknown')
            if lang not in languages or len(selected)>=3:
                selected.append(s); languages.add(lang)
            if len(selected)>=max_per_region: break
        chosen.extend(selected)
    return chosen

def _health_ok(report):
    """A source is live-useful only when extraction yielded dated material."""
    return (
        report.get('status') in ('active','social_only')
        and int(report.get('items') or 0) > 0
        and int(report.get('dated_items') or 0) > 0
    )

def health_summary(health):
    """Summarize live extractor health by monitored region."""
    regions={}
    for region in REGIONS:
        reports=[r for r in health if r.get('region')==region]
        healthy=[r for r in reports if _health_ok(r)]
        regions[region]={
          'checked':len(reports),
          'healthy_extractors':len({r.get('id') for r in healthy if r.get('id')}),
          'active_source_ids':sorted({r.get('id') for r in healthy if r.get('id')}),
          'substitutes_used':sum(bool(r.get('substitute')) and _health_ok(r) for r in reports),
        }
    unresolved=[r for r,v in regions.items() if not v['healthy_extractors']]
    return {'regions':regions,'unresolved_regions':unresolved,'all_regions_healthy':not unresolved}

def _collect_batch(sources,discover=False,substitute_ids=None):
    items=[]; health=[]
    substitute_ids=set(substitute_ids or ())
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures={pool.submit(collect_source,s,discover):s for s in sources}
        for future in as_completed(futures):
            source=futures[future]
            try:
                found,report=future.result()
            except Exception as e:
                found=[]; report={'id':source['id'],'name':source['name'],'region':source['region'],
                  'country':source['country'],'language':source.get('language','unknown'),
                  'status':'failed','items':0,'dated_items':0,'errors':[type(e).__name__],'social':[]}
            if source['id'] in substitute_ids:
                report['substitute']=True
            items.extend(found); health.append(report)
    return items,health

def _finalize(items,start,end):
    seen=set(); selected=[]
    for item in sorted(items,key=lambda x:x['published'] or 0,reverse=True):
        if not item['published'] or not start.timestamp() <= item['published'] < end.timestamp(): continue
        material=item['title']+' '+item['text']
        if not source_relevant(item,material): continue
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
    return balanced

def collect(start,end,discover=False,registry=None,repair_unhealthy=True):
    """Collect current evidence and automatically repair unhealthy regional coverage.

    The first pass uses normal production sources. If any monitored region has no
    live extractor yielding dated material, alternate publishers from that SAME
    region are probed (including disabled/previously failed audit candidates).
    This prevents a stale feed from silently becoming a geographic coverage gap.
    """
    sources=registry or json.loads((ROOT/'sources.json').read_text())
    selected_sources=sources if discover else production_sources(sources,end)
    items,health=_collect_batch(selected_sources,discover)
    if not discover and repair_unhealthy:
        attempted={s['id'] for s in selected_sources}
        summary=health_summary(health)
        substitutes=[]
        for region in summary['unresolved_regions']:
            candidates=[s for s in sources if s.get('region')==region and s.get('id') not in attempted]
            # Prefer sources that were historically active, then enabled sources,
            # while retaining language diversity. Every candidate remains same-region.
            candidates.sort(key=lambda s:(
                s.get('verification_status')!='active',
                s.get('enabled') is False,
                s.get('language')=='ar',
                s.get('id','')))
            substitutes.extend(candidates[:6])
        if substitutes:
            substitute_ids={s['id'] for s in substitutes}
            extra_items,extra_health=_collect_batch(substitutes,True,substitute_ids)
            items.extend(extra_items); health.extend(extra_health)
    return _finalize(items,start,end),sorted(health,key=lambda x:(x.get('region',''),x.get('id','')))

def audit(output):
    sources=json.loads((ROOT/'sources.json').read_text()); reports=[]; discovered=[]
    with ThreadPoolExecutor(max_workers=8) as pool:
        # Audit the whole registry. A transient failure must not permanently
        # exclude a source from future recovery checks.
        futures={pool.submit(collect_source,s,True):s for s in sources}
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
