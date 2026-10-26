"""Generate source-safe synthetic EN/AR HTML for offline browser QA only."""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from tempfile import mkdtemp

from v2_b18_private_digest import make_private_digest
from v2_b20_private_mobile import render_private_mobile


def generate(output_dir=None):
    dest = Path(output_dir) if output_dir is not None else Path(mkdtemp(prefix='aggregateit-b32-'))
    if not dest.exists():
        dest.mkdir(parents=True)
    if not dest.is_dir() or any(dest.iterdir()):
        raise ValueError('unsafe_fixture_output_directory')
    result = {'schema': 'aggregateit-v2-b32-browser-fixture/1',
              'output_dir': str(dest), 'products': {}}
    content = {
        'english': ['Regional developments and source-specific analysis remain unverified',
                    'Markets and macro indicators: the verified observation is unavailable',
                    'A long secondary security headline checks mobile wrapping and clipping'],
        'arabic': ['تطورات إقليمية وتحليل مرتبط بالمصدر لم يخضع للتحقق المستقل بعد',
                   'حالة الأمن الإقليمي مع الاحتفاظ بالنص العربي الأصلي دون ترجمة آلية',
                   'عنوان عربي طويل لاختبار عرض الهاتف ولف السطور واتجاه النص'],
    }
    for product, titles in content.items():
        lang = 'ar' if product == 'arabic' else 'en'
        rows = [{'candidate_id': 'synthetic-' + str(i), 'excerpt_id': 'fixture-' + str(i),
                 'source_id': 'SYNTHETIC-SOURCE', 'article_url': 'https://example.org/test/' + str(i),
                 'title': title, 'quote': ('هذا مثال اصطناعي لا يحتوي على بيانات إخبارية حقيقية.' if lang == 'ar'
                                             else 'This is synthetic text, not a current-news assertion.'),
                 'region': ['gcc', 'yemen', 'iran'][i], 'original_language': lang,
                 'topic': 'security' if lang == 'ar' else ('finance' if i == 1 else 'security')}
                for i, title in enumerate(titles)]
        digest = make_private_digest(product=product,
                   slot_id='2026-10-26T06:00:00+04:00', stories=rows,
                   missing_regions=['jordan', 'somalia', 'egypt'])
        html = render_private_mobile(digest).encode('utf8')
        path = dest / (product + '.html')
        path.write_bytes(html)
        result['products'][product] = {'path': str(path), 'sha256': sha256(html).hexdigest(),
                                       'expected_stories': len(rows)}
    return result


if __name__ == '__main__':
    print(json.dumps(generate(), ensure_ascii=False))
