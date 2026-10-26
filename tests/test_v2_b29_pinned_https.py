"""B29/B30 regression: DNS policy is enforced on actual TCP destination."""
import socket
import ssl
import unittest
from unittest.mock import Mock, patch
from urllib.error import HTTPError

from v2_secure_transport import _origin_and_path, _public_ips, pinned_https_fetch


def resolver(host, port, *, type):
    assert port == 443 and type == socket.SOCK_STREAM
    return [(socket.AF_INET, socket.SOCK_STREAM, 6, '', ('8.8.8.8', 443)),
            (socket.AF_INET, socket.SOCK_STREAM, 6, '', ('1.1.1.1', 443))]


def packet(status=200, location=None):
    headers={'Content-Type':'text/xml'}
    if location:headers['Location']=location
    return {'status':status,'headers':headers,'body':b'<rss/>'}


class PinnedTransportTests(unittest.TestCase):
    def test_rejects_unsafe_origins(self):
        for url in ('http://example.org/x','https://localhost/x',
                    'https://127.1/x','https://0x7f000001/x',
                    'https://user:pass@example.org/x','https://example.org:8443/x',
                    'https://example.org/x#fragment','https://10.0.0.2/x'):
            with self.subTest(url=url), self.assertRaises(ValueError):
                _origin_and_path(url)

    def test_public_dns_returns_numeric_literals(self):
        self.assertEqual(_public_ips('example.org',resolver), ('8.8.8.8','1.1.1.1'))

    def test_caller_cannot_override_pinned_host(self):
        with patch('v2_secure_transport._connect_pinned') as conn:
            with self.assertRaisesRegex(ValueError, 'invalid_request_header'):
                pinned_https_fetch('https://example.org/rss', resolver=resolver,
                                   headers={'Host': 'internal.local'})
            conn.assert_not_called()

    def test_mixed_dns_refuses_before_tcp(self):
        bad=lambda host,port,*,type: resolver(host,port,type=type)+[(2,1,6,'',('127.0.0.1',443))]
        with patch('v2_secure_transport._connect_pinned') as conn:
            with self.assertRaisesRegex(ValueError,'unsafe_resolved_ip'):
                pinned_https_fetch('https://example.org/rss',resolver=bad)
            conn.assert_not_called()

    def test_resolution_empty_refused(self):
        with self.assertRaisesRegex(ValueError,'dns_resolution_empty'):
            pinned_https_fetch('https://example.org/rss',resolver=lambda *a,**k: [])

    def test_connects_to_prevalidated_ip_without_hostname_resolution(self):
        with patch('v2_secure_transport._connect_pinned',return_value=packet()) as conn:
            result=pinned_https_fetch('https://example.org/rss',resolver=resolver)
        self.assertEqual(result['body'],b'<rss/>')
        self.assertEqual(conn.call_args.args[:3],('example.org','8.8.8.8','/rss'))

    def test_socket_failure_can_try_second_public_address(self):
        with patch('v2_secure_transport._connect_pinned',side_effect=[OSError('offline'),packet()]) as conn:
            result=pinned_https_fetch('https://example.org/rss',resolver=resolver)
        self.assertEqual(result['status'],200)
        self.assertEqual(conn.call_count,2)

    def test_http_403_never_retries_secondary_ip(self):
        with patch('v2_secure_transport._connect_pinned',return_value=packet(403)) as conn:
            with self.assertRaises(HTTPError) as raised:
                pinned_https_fetch('https://example.org/rss',resolver=resolver)
        self.assertEqual(raised.exception.code,403)
        self.assertEqual(conn.call_count,1)

    def test_http_429_never_retries_secondary_ip(self):
        with patch('v2_secure_transport._connect_pinned',return_value=packet(429)) as conn:
            with self.assertRaises(HTTPError):
                pinned_https_fetch('https://example.org/rss',resolver=resolver)
        self.assertEqual(conn.call_count,1)

    def test_tls_error_never_retries_secondary_ip(self):
        with patch('v2_secure_transport._connect_pinned',side_effect=ssl.SSLError('bad certificate')) as conn:
            with self.assertRaises(ssl.SSLError):
                pinned_https_fetch('https://example.org/rss',resolver=resolver)
        self.assertEqual(conn.call_count,1)

    def test_same_origin_redirect_re_resolves_and_pins(self):
        counter=Mock(side_effect=resolver)
        with patch('v2_secure_transport._connect_pinned',side_effect=[packet(302,'/new'),packet()]) as conn:
            result=pinned_https_fetch('https://example.org/old',resolver=counter)
        self.assertEqual(result['final_url'],'https://example.org/new')
        self.assertEqual(counter.call_count,2)
        self.assertEqual(conn.call_args.args[2],'/new')

    def test_cross_origin_redirect_refused_without_second_connection(self):
        with patch('v2_secure_transport._connect_pinned',return_value=packet(302,'https://other.org/rss')) as conn:
            with self.assertRaisesRegex(ValueError,'cross_origin_redirect_refused'):
                pinned_https_fetch('https://example.org/rss',resolver=resolver)
        self.assertEqual(conn.call_count,1)

    def test_redirect_limit_including_disabled_pilot(self):
        with patch('v2_secure_transport._connect_pinned',return_value=packet(302,'/more')) as conn:
            with self.assertRaisesRegex(ValueError,'redirect_limit_exceeded'):
                pinned_https_fetch('https://example.org/rss',max_redirects=0,resolver=resolver)
        self.assertEqual(conn.call_count,1)

    def test_feed_wrapper_uses_pinned_transport(self):
        from v2_feed_probe import bounded_fetch
        with patch('v2_feed_probe.pinned_https_fetch',return_value={'body':b'<rss/>'}) as conn:
            self.assertEqual(bounded_fetch('https://example.org/feed'),b'<rss/>')
        self.assertEqual(conn.call_args.kwargs['max_redirects'],2)

    def test_regional_adapter_refuses_non_xml(self):
        from v2_large_feed_adapter import _fetch_registered_feed
        with patch('v2_large_feed_adapter.pinned_https_fetch',return_value={
                'final_url':'https://shafaq.com/rss/ar','status':200,
                'content_type':'text/html','body':b'<rss/>'}):
            with self.assertRaisesRegex(ValueError,'not_xml_content_type'):
                _fetch_registered_feed('https://shafaq.com/rss/ar',timeout=8,max_bytes=1000000)

    def test_a8_wrapper_disallows_redirects(self):
        from v2_a8_single_run import _live_html_fetch
        with patch('v2_a8_single_run.pinned_https_fetch',return_value={
                'final_url':'https://www.bbc.co.uk/news/x','status':200,
                'content_type':'text/html','body':b'<html/>'}) as conn:
            self.assertEqual(_live_html_fetch('https://www.bbc.co.uk/news/x',timeout=8)['status'],200)
        self.assertEqual(conn.call_args.kwargs['max_redirects'],0)


if __name__ == '__main__':
    unittest.main()
