"""Bounded read-only RSS/Atom health probe. Does not alter registry or publish."""
from __future__ import annotations
from datetime import datetime,timezone
from email.utils import parsedate_to_datetime
import ipaddress,urllib.request
from urllib.parse import urlsplit
from xml.etree import ElementTree as ET

MAX_BYTES=200000

def _date(value):
    if not isinstance(value,str) or not value:return None
    for parser in (lambda: datetime.fromisoformat(value.replace('Z','+00:00')),
                   lambda: parsedate_to_datetime(value)):
        try:
            dt=parser()
            if dt.utcoffset() is not None:return dt.astimezone(timezone.utc)
        except (ValueError,TypeError,OverflowError):
            continue
    return None

def _url_safe(url):
    if not isinstance(url,str):raise ValueError('invalid_feed_url')
    obj=urlsplit(url)
    if obj.scheme!='https' or obj.username or obj.password or not obj.hostname:
        raise ValueError('unsafe_feed_url')
    host=obj.hostname.lower()
    if host=='localhost' or host.endswith(('.local','.internal','.test','.invalid')):
        raise ValueError('unsafe_feed_url')
    try:
        ip=ipaddress.ip_address(host)
        if not ip.is_global:raise ValueError('unsafe_feed_url')
    except ValueError as exc:
        if str(exc)=='unsafe_feed_url':raise
    return url

class _SafeRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        _url_safe(newurl)
        return super().redirect_request(req,fp,code,msg,headers,newurl)

def bounded_fetch(url,*,timeout=8):
    _url_safe(url)
    if not isinstance(timeout,(float,int)) or not 1<=timeout<=12:raise ValueError('unsafe_timeout')
    opener=urllib.request.build_opener(_SafeRedirect())
    req=urllib.request.Request(url,headers={'User-Agent':'AggregateIT-V2-research/1.0'})
    with opener.open(req,timeout=timeout) as response:
        return response.read(MAX_BYTES+1)

def inspect_feed_bytes(body,*,now,max_age_hours=72):
    if not isinstance(body,bytes):raise ValueError('bytes_required')
    if not 1<=max_age_hours<=168:raise ValueError('invalid_freshness_age')
    current=_date(now)
    if current is None:raise ValueError('timezone_required')
    result={'schema':'aggregateit-feed-observation/1','status':'unknown','entry_count':0,
            'dated_count':0,'recent_count':0,'newest_item_at':None,
            'article_bodies_retained':False,'publisher_independence':'unverified'}
    if len(body)>MAX_BYTES:
        result['status']='oversized_body';return result
    try:root=ET.fromstring(body)
    except ET.ParseError:
        result['status']='invalid_xml';return result
    root_name=root.tag.rsplit('}',1)[-1].lower()
    if root_name=='rss':items=root.findall('./channel/item')
    elif root_name=='feed':items=[x for x in root if x.tag.rsplit('}',1)[-1]=='entry']
    elif root_name=='rdf':items=[x for x in root if x.tag.rsplit('}',1)[-1]=='item']
    else:
        result['status']='not_a_feed';return result
    result['entry_count']=len(items)
    dates=[]
    for item in items:
        children={e.tag.rsplit('}',1)[-1].lower():e.text for e in item}
        raw=children.get('updated') or children.get('published') or children.get('pubdate') or children.get('date')
        dt=_date(raw)
        if dt is not None:dates.append(dt)
    result['dated_count']=len(dates)
    result['recent_count']=sum(-300<=(current-d).total_seconds()<=max_age_hours*3600 for d in dates)
    result['newest_item_at']=max(dates).isoformat() if dates else None
    result['status']=('empty_feed' if not items else 'undated_feed' if not dates
                      else 'stale_feed' if not result['recent_count'] else 'usable_dated_feed')
    return result
