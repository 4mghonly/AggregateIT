"""HTTPS-only transport with public-IP pinning and bounded redirects.

The DNS answers validated for a request are the addresses used by its TCP
connection. HTTPS SNI, hostname verification and Host keep the original name.
This is an in-process defense, not a substitute for an egress firewall.
"""
from __future__ import annotations

import http.client
import ipaddress
import socket
import ssl
from urllib.error import HTTPError
from urllib.parse import urljoin, urlsplit


def _origin_and_path(url: str) -> tuple[str, str]:
    if not isinstance(url, str) or not 1 <= len(url) <= 2048:
        raise ValueError('invalid_https_url')
    try:
        p = urlsplit(url)
        port = p.port
    except ValueError as exc:
        raise ValueError('invalid_https_url') from exc
    if (p.scheme != 'https' or not p.hostname or port not in (None, 443)
            or p.username is not None or p.password is not None or p.fragment):
        raise ValueError('unsafe_https_url')
    host = p.hostname.lower().rstrip('.')
    if (not host or host == 'localhost' or host.endswith(('.localhost', '.local',
            '.internal', '.test', '.invalid'))):
        raise ValueError('unsafe_https_url')
    # Legacy numeric aliases such as 127.1 and 0x7f000001 are not IP literals
    # to ipaddress, but can resolve as loopback on common libc implementations.
    components = host.split('.')
    if components and all(c.isdecimal() or c.lower().startswith('0x') for c in components):
        raise ValueError('unsafe_https_url')
    try:
        if not ipaddress.ip_address(host).is_global:
            raise ValueError('unsafe_https_url')
    except ValueError as exc:
        if str(exc) == 'unsafe_https_url':
            raise
    return host, (p.path or '/') + (('?' + p.query) if p.query else '')


def _public_ips(host: str, resolver=None) -> tuple[str, ...]:
    answers = (resolver or socket.getaddrinfo)(host, 443, type=socket.SOCK_STREAM)
    if not answers:
        raise ValueError('dns_resolution_empty')
    ips: list[str] = []
    for record in answers:
        try:
            candidate = ipaddress.ip_address(record[4][0])
        except (IndexError, TypeError, ValueError) as exc:
            raise ValueError('unsafe_resolved_ip') from exc
        if not candidate.is_global:
            raise ValueError('unsafe_resolved_ip')
        if str(candidate) not in ips:
            ips.append(str(candidate))
    return tuple(ips)


class _PinnedHTTPSConnection(http.client.HTTPSConnection):
    def __init__(self, host: str, address: str, *, timeout: float):
        super().__init__(host, port=443, timeout=timeout, context=ssl.create_default_context())
        self._numeric_address = address

    def connect(self) -> None:
        sock = socket.create_connection((self._numeric_address, 443), self.timeout)
        try:
            self.sock = self._context.wrap_socket(sock, server_hostname=self.host)
        except BaseException:
            sock.close()
            raise


def _connect_pinned(host: str, address: str, path: str, *, timeout: float,
                    headers: dict[str, str], max_bytes: int) -> dict:
    conn = _PinnedHTTPSConnection(host, address, timeout=timeout)
    try:
        conn.request('GET', path, headers={'Host': host, **headers})
        response = conn.getresponse()
        body = response.read(max_bytes + 1)
        return {'status': response.status, 'headers': dict(response.getheaders()), 'body': body}
    finally:
        conn.close()


def pinned_https_fetch(url: str, *, timeout: float = 8, max_bytes: int = 200000,
                       max_redirects: int = 2, headers: dict[str, str] | None = None,
                       resolver=None) -> dict:
    """Fetch through only a validated public IP; never follow other origins.

    Returns status/content_type/final_url/body for 2xx responses. Raises
    HTTPError for other terminal HTTP codes and ValueError for redirect policy.
    No alternate IP is tried after an HTTP response or a TLS failure.
    """
    if (not isinstance(timeout, (float, int)) or isinstance(timeout, bool)
            or not 1 <= timeout <= 12):
        raise ValueError('unsafe_timeout')
    if type(max_bytes) is not int or not 1 <= max_bytes <= 1000000:
        raise ValueError('unsafe_byte_budget')
    if type(max_redirects) is not int or not 0 <= max_redirects <= 2:
        raise ValueError('unsafe_redirect_budget')
    if not isinstance(headers or {}, dict) or any(
            not isinstance(k, str) or not isinstance(v, str)
            or k.lower() in {'host', 'connection', 'content-length', 'transfer-encoding'}
            for k, v in (headers or {}).items()):
        raise ValueError('invalid_request_header')
    request_headers = {'User-Agent': 'AggregateIT-V2-PinnedReadOnly/1.0',
                       'Accept-Encoding': 'identity', **(headers or {})}
    if any('\r' in k + v or '\n' in k + v for k, v in request_headers.items()):
        raise ValueError('invalid_request_header')
    first_host, _ = _origin_and_path(url)
    current = url
    for redirect in range(max_redirects + 1):
        host, path = _origin_and_path(current)
        if host != first_host:
            raise ValueError('cross_origin_redirect_refused')
        addresses = _public_ips(host, resolver=resolver)
        packet = None
        for index, address in enumerate(addresses):
            try:
                packet = _connect_pinned(host, address, path, timeout=timeout,
                                         headers=request_headers, max_bytes=max_bytes)
                break
            except ssl.SSLError:
                raise
            except (socket.timeout, OSError):
                if index == len(addresses) - 1:
                    raise
        if packet is None:
            raise ValueError('dns_resolution_empty')
        status = packet['status']
        h = {str(k).lower(): str(v) for k, v in packet['headers'].items()}
        if status in (301, 302, 303, 307, 308):
            if redirect >= max_redirects:
                raise ValueError('redirect_limit_exceeded')
            target = h.get('location')
            if not target:
                raise ValueError('redirect_without_location')
            current = urljoin(current, target)
            destination, _ = _origin_and_path(current)
            if destination != first_host:
                raise ValueError('cross_origin_redirect_refused')
            continue
        if status < 200 or status >= 300:
            raise HTTPError(current, status, f'http_{status}', h, None)
        return {'status': status, 'content_type': h.get('content-type', ''),
                'final_url': current, 'body': packet['body']}
    raise ValueError('redirect_limit_exceeded')
