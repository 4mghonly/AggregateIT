"""No-post, no-model, stdlib-only read-only RSS/Atom health lab.

Unlike the legacy collectors, these bounded diagnostics do not require
feedparser, trafilatura, or ddgs. They do not prove a publisher's licensing,
identity, or factual reliability; the output cannot authorize publication.
External network is OPT-IN, one GET per unique HTTPS URL, max 12 sources.
"""
from __future__ import annotations

from datetime import datetime
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit

from v2_feed_probe import _date, _url_safe, bounded_fetch, inspect_feed_bytes
from v2_feed_items import extract_candidates

MAX_SOURCES = 12


def probe_source_batch(sources, *, now: str, fetcher=None,
                       allow_network: bool = False, timeout: int = 8) -> dict:
    if not isinstance(sources, list) or len(sources) > MAX_SOURCES:
        raise ValueError('source_budget_exceeded')
    if _date(now) is None:
        raise ValueError('timezone_required')
    if type(timeout) not in (int, float) or not 1 <= timeout <= 12:
        raise ValueError('unsafe_timeout')
    if fetcher is None and not allow_network:
        raise ValueError('network_opt_in_required')
    getter = fetcher if fetcher is not None else bounded_fetch
    output = []
    seen = set()
    for source in sources:
        if not isinstance(source, dict) or not isinstance(source.get('source_id'), str):
            raise ValueError('invalid_source_record')
        sid = source['source_id']
        url = source.get('url')
        obs = {'source_id': sid, 'url': url, 'status': 'unprobed',
               'candidate_count': 0, 'recent_count': 0,
               'entry_count': 0, 'publisher_family_verified': False,
               'article_bodies_retained': False, 'publishable': False}
        try:
            _url_safe(url)
        except (ValueError, TypeError):
            obs['status'] = 'unsafe_source_url'
            output.append(obs)
            continue
        canon = urlsplit(url)._replace(fragment='').geturl().rstrip('/')
        if canon in seen:
            obs['status'] = 'duplicate_url_not_probed'
            output.append(obs)
            continue
        seen.add(canon)
        try:
            raw = getter(url, timeout=timeout)
        except ValueError as exc:
            obs['status'] = ('unsafe_source_url' if str(exc).startswith(('unsafe_resolved_ip', 'dns_resolution_empty')) else 'invalid_feed_response')
        except HTTPError as exc:
            obs['status'] = f'http_{int(exc.code)}'
        except (TimeoutError, URLError, OSError):
            obs['status'] = 'network_error'
        else:
            result = inspect_feed_bytes(raw, now=now)
            obs['status'] = result['status']
            obs['recent_count'] = result['recent_count']
            obs['entry_count'] = result['entry_count']
            obs['newest_item_at'] = result.get('newest_item_at')
            if result['status'] == 'usable_dated_feed':
                items = extract_candidates(raw, feed_url=url, observed_at=now,
                                           max_items=30)
                obs['candidate_count'] = items['candidate_count']
        output.append(obs)
    return {'schema': 'aggregateit-v2-source-lab/1',
            'checked_at': datetime.fromisoformat(now.replace('Z','+00:00')).isoformat(),
            'sources': output,
            'live_http_performed': fetcher is None and allow_network,
            'source_independence_verified': False,
            'production_promoted': False,
            'discord_sent': False, 'model_called': False}


def main(argv=None) -> int:
    """CLI: offline manifest by default; --live enables bounded GET-only checks."""
    import argparse
    import json
    from datetime import timezone
    from datetime import datetime as _dt

    cli=argparse.ArgumentParser(description='Read-only V2 source compatibility lab; never publishes')
    cli.add_argument('--source',action='append',default=[],metavar='ID=HTTPS_URL',
                     help='At most 12 source IDs and HTTPS RSS/Atom URLs')
    cli.add_argument('--now',default=_dt.now(timezone.utc).isoformat())
    cli.add_argument('--live',action='store_true',help='Explicitly opt into bounded public HTTPS GET checks')
    args=cli.parse_args(argv)
    if not args.source or len(args.source)>MAX_SOURCES:
        cli.error('supply 1 to 12 --source entries')
    sources=[]
    for item in args.source:
        if '=' not in item:
            cli.error('--source must be ID=HTTPS_URL')
        sid,url=item.split('=',1)
        if not sid or not url:
            cli.error('--source needs a nonempty ID and URL')
        sources.append({'source_id':sid,'url':url})
    if args.live:
        result=probe_source_batch(sources,now=args.now,allow_network=True)
    else:
        result={'schema':'aggregateit-v2-source-lab/1',
                'status':'dry_run_only','live_http_performed':False,
                'sources':sources,'source_independence_verified':False,
                'production_promoted':False,'model_called':False,
                'discord_sent':False}
    print(json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True))
    return 0


if __name__=='__main__':
    raise SystemExit(main())
