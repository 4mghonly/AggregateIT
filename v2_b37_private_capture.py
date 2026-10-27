"""B37 ephemeral no-post source-headline browser fixture generation.

Only sanitized counts/digests become runner reports. Source bytes, titles,
links and HTML stay in the runner's temporary directory, never GitHub artifacts.
"""
from __future__ import annotations
import json
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from tempfile import mkdtemp
from v2_feed_items import extract_candidates
from v2_secure_transport import pinned_https_fetch
from v2_b37_mobile_headlines import render_source_watch_html

SOURCES = {'english': 'https://feeds.bbci.co.uk/news/world/rss.xml',
           'arabic': 'https://www.aljazeera.net/aljazeerarss/ar/all.xml'}


def run() -> dict:
    root=Path(mkdtemp(prefix='aggregateit-b37-'))
    data={'schema':'aggregateit-v2-b37-runner-fixture/1','temp_dir':str(root),
          'source_bytes_retained':False, 'discord_sent':False,'results':{}}
    for product,url in SOURCES.items():
        row={'status':'hold','feed_url':url,'article_body_verified':False}
        try:
            packet=pinned_https_fetch(url,timeout=9,max_bytes=1_000_000,max_redirects=1,
                         headers={'Accept':'application/rss+xml, application/xml, text/xml'})
            raw=packet['body']
            now=datetime.now(timezone.utc).isoformat()
            parsed=extract_candidates(raw,feed_url=packet['final_url'],observed_at=now,
                                      max_items=30,max_age_hours=72,max_bytes=1_000_000)
            view=render_source_watch_html(product,parsed['items'],now)
            page=view['html'].encode('utf8')
            path=root / (product+'.html')
            path.write_bytes(page)
            row.update({'status':'captured' if view['shown'] else 'empty',
                        'capture_sha256':sha256(raw).hexdigest(),
                        'capture_bytes':len(raw),
                        'page_sha256':sha256(page).hexdigest(),
                        'page_file':str(path),
                        'headlines_shown':view['shown'],
                        'script_filtered':view['script_filtered'],
                        'candidate_count':parsed['candidate_count']})
        except Exception as exc:
            row['failure_class']=type(exc).__name__
        data['results'][product]=row
    return data

if __name__ == '__main__':
    print(json.dumps(run(),ensure_ascii=False))
