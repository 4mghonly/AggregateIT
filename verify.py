"""verify.py — independent corroboration of event claims via DuckDuckGo search.
Returns distinct domains mentioning the event; degrades gracefully offline."""
from urllib.parse import urlparse

def verify_event(title, max_results=8):
    try:
        from ddgs import DDGS
        with DDGS() as d:
            res = d.text(title, max_results=max_results)
        domains = set()
        for r in (res or []):
            dom = urlparse(r.get("href", "")).netloc.lower()
            if dom.startswith("www."): dom = dom[4:]
            if dom: domains.add(dom)
        return sorted(domains)
    except Exception:
        return []
