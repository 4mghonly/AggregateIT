"""B21 private immutable snapshot receipts; caller controls actual storage."""
from __future__ import annotations

from hashlib import sha256


def capture_private_snapshot(*, filename: str, content: bytes, product: str,
                             media_type: str, observed_at: str) -> dict:
    if product not in ('english', 'arabic') or media_type not in ('text/html', 'image/png', 'application/pdf'):
        raise ValueError('invalid_private_snapshot_type')
    if (not isinstance(filename, str) or '/' in filename or '\\' in filename
            or not 1 <= len(filename) <= 120):
        raise ValueError('invalid_snapshot_name')
    if not isinstance(content, bytes) or not 1 <= len(content) <= 8 * 1024 * 1024:
        raise ValueError('invalid_snapshot_bytes')
    if media_type == 'image/png' and not content.startswith(b'\x89PNG\r\n\x1a\n'):
        raise ValueError('invalid_png_header')
    if media_type == 'application/pdf' and not content.startswith(b'%PDF-'):
        raise ValueError('invalid_pdf_header')
    if media_type == 'text/html' and not content.lstrip().lower().startswith(b'<!doctype html>'):
        raise ValueError('invalid_html_header')
    from v2_b18_private_digest import _slot
    return {'schema': 'aggregateit-v2-b21-private-snapshot/1', 'filename': filename,
            'product': product, 'media_type': media_type, 'observed_at': _slot(observed_at),
            'size_bytes': len(content), 'sha256': sha256(content).hexdigest(),
            'bytes_retained_in_receipt': False, 'private_only': True, 'discord_sent': False}


def verify_private_snapshot(receipt: dict, content: bytes) -> bool:
    return (isinstance(receipt, dict) and receipt.get('private_only') is True
            and isinstance(content, bytes) and len(content) == receipt.get('size_bytes')
            and sha256(content).hexdigest() == receipt.get('sha256'))
