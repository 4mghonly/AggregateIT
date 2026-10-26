"""B23 pure compact mobile layout metrics; no implicit screenshot claims."""
from __future__ import annotations

from html.parser import HTMLParser


class _PrivatePreviewParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.headings = 0
        self.articles = 0
        self.viewport = False
        self.lang = None
        self.direction = None

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == 'html':
            self.lang = values.get('lang')
            self.direction = values.get('dir')
        if tag == 'meta' and values.get('name') == 'viewport':
            self.viewport = 'width=device-width' in values.get('content', '')
        self.headings += tag == 'h1'
        self.articles += tag == 'article'


def audit_compact_markup(html: str, *, product: str, expected_stories: int) -> dict:
    if not isinstance(html, str) or product not in ('english', 'arabic'):
        raise ValueError('invalid_mobile_markup')
    p = _PrivatePreviewParser()
    p.feed(html)
    required_lang, required_direction = ('ar', 'rtl') if product == 'arabic' else ('en', 'ltr')
    checks = {'viewport': p.viewport, 'document_language': p.lang == required_lang,
              'text_direction': p.direction == required_direction, 'one_page_heading': p.headings == 1,
              'story_card_count': p.articles == expected_stories,
              'responsive_css': 'overflow-wrap:anywhere' in html and 'max-width:950px' in html}
    return {'schema': 'aggregateit-v2-b23-markup-audit/1', 'checks': checks,
            'static_checks_passed': all(checks.values()),
            'real_device_verified': False, 'screenshot_verified': False,
            'delivery_authorized': False}
