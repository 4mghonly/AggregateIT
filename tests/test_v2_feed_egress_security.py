"""RSS adapters refuse XML entity expansion and private DNS results."""
import socket
import unittest
from unittest.mock import patch
from v2_feed_probe import inspect_feed_bytes, _assert_public_dns
from v2_feed_items import extract_candidates
from v2_source_lab import probe_source_batch

NOW='2026-10-24T06:00:00+04:00'
BAD=(b'<!DOCTYPE rss [<!ENTITY xx "a very long expansion">]>'
     b'<rss><channel><item><title>&xx;</title></item></channel></rss>')

class EgressSafetyTests(unittest.TestCase):
    def test_dtd_rejected_before_metadata_parse(self):
        result=inspect_feed_bytes(BAD,now=NOW)
        self.assertEqual(result['status'],'invalid_xml')
    def test_dtd_rejected_before_candidate_extraction(self):
        with self.assertRaisesRegex(ValueError,'invalid_feed_xml'):
            extract_candidates(BAD,feed_url='https://example.org/rss',observed_at=NOW)
    def test_dns_private_result_refused(self):
        def resolver(host,port,*,type):
            return [(socket.AF_INET,socket.SOCK_STREAM,6,'',('10.0.0.2',port))]
        with self.assertRaisesRegex(ValueError,'unsafe_resolved_ip'):
            _assert_public_dns('news.example.org',resolver=resolver)
    def test_dns_mixed_private_and_public_refused(self):
        def resolver(host,port,*,type):
            return [(socket.AF_INET,socket.SOCK_STREAM,6,'',('8.8.8.8',port)),
                    (socket.AF_INET,socket.SOCK_STREAM,6,'',('127.0.0.1',port))]
        with self.assertRaisesRegex(ValueError,'unsafe_resolved_ip'):
            _assert_public_dns('news.example.org',resolver=resolver)
    def test_dns_public_result_allowed(self):
        def resolver(host,port,*,type):
            return [(socket.AF_INET,socket.SOCK_STREAM,6,'',('8.8.8.8',port))]
        self.assertIsNone(_assert_public_dns('news.example.org',resolver=resolver))
    def test_batch_records_private_dns_refusal_without_fetching(self):
        def resolver(host,port,*,type):
            return [(socket.AF_INET,socket.SOCK_STREAM,6,'',('169.254.169.254',port))]
        with patch('v2_feed_probe.socket.getaddrinfo',side_effect=resolver):
            out=probe_source_batch([{'source_id':'x','url':'https://news.example.org/rss'}],
                                   now=NOW,allow_network=True)
        self.assertEqual(out['sources'][0]['status'],'unsafe_source_url')

if __name__=='__main__':unittest.main()
