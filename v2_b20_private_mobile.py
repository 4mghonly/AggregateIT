"""B20 read-only responsive mobile preview for private evidence digests."""
from __future__ import annotations

from html import escape


def render_private_mobile(digest: dict) -> str:
    if (not isinstance(digest, dict) or digest.get('schema') != 'aggregateit-v2-b18-private-digest/1'
            or digest.get('private_only') is not True or digest.get('delivery_authorized') is not False):
        raise ValueError('untrusted_private_digest')
    ar = digest.get('product') == 'arabic'
    if not ar and digest.get('product') != 'english':
        raise ValueError('invalid_digest_product')
    heading = 'موجز الرصد الخاص' if ar else 'PRIVATE INTELLIGENCE BRIEF'
    note = 'مراجعة تحليلية خاصة — غير منشور' if ar else 'PRIVATE ANALYST REVIEW · NOT PUBLISHED'
    missing = 'مناطق بلا أدلة كافية' if ar else 'Coverage gaps'
    cards = []
    for s in digest.get('stories', []):
        if s.get('original_language') != ('ar' if ar else 'en'):
            raise ValueError('native_language_mismatch')
        cards.append('<article class="story"><div class="meta">' + escape(s['region']) + ' · '
                     + escape(s['source_id']) + '</div><h2>' + escape(s['title'])
                     + '</h2><blockquote>' + escape(s['quote']) + '</blockquote><small>'
                     + escape(s['excerpt_id']) + '</small></article>')
    gaps = ', '.join(escape(x) for x in digest.get('missing_regions', [])) or ('—' if ar else 'None recorded')
    return ('<!doctype html><html lang="' + ('ar' if ar else 'en') + '" dir="' + ('rtl' if ar else 'ltr')
            + '"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            + '<title>' + heading + '</title><style>*{box-sizing:border-box}body{margin:0;background:#101c28;'
            + 'color:#f2f3ec;font-family:system-ui,sans-serif;line-height:1.5}main{max-width:950px;margin:auto;padding:24px}'
            + 'header{border-bottom:2px solid #d2ad7b;padding:12px 0 24px}h1{font-size:clamp(25px,5vw,45px);'
            + 'line-height:1.12;margin:8px 0}p,.meta,small{color:#b8cbd2}.story{padding:20px 0;border-bottom:1px solid #416076}'
            + 'h2{font-size:clamp(22px,4vw,33px);line-height:1.32;margin:10px 0}blockquote{margin:0;padding:12px 18px;'
            + 'border-inline-start:3px solid #d2ad7b;background:#1c3140;overflow-wrap:anywhere}'
            + '.meta{font-size:13px;letter-spacing:.02em}small{overflow-wrap:anywhere}</style></head><body><main>'
            + '<header><p>' + escape(note) + '</p><h1>' + heading + '</h1><p>'
            + escape(digest['slot_id']) + '</p></header>' + ''.join(cards) + '<footer><h2>'
            + escape(missing) + '</h2><p>' + gaps + '</p></footer></main></body></html>')
