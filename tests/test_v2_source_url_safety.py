"""Block obvious loopback alias URL forms before feed fetching."""
import unittest
from v2_feed_probe import _url_safe


class FeedUrlSafetyTests(unittest.TestCase):
    def test_localhost_fqdn_alias_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'unsafe_feed_url'):
            _url_safe('https://localhost./rss')

    def test_short_ipv4_alias_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'unsafe_feed_url'):
            _url_safe('https://127.1/rss')

    def test_hex_ipv4_alias_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'unsafe_feed_url'):
            _url_safe('https://0x7f000001/rss')

    def test_standard_public_host_allowed(self):
        self.assertEqual(_url_safe('https://feeds.bbci.co.uk/news/world/rss.xml'),
                         'https://feeds.bbci.co.uk/news/world/rss.xml')
