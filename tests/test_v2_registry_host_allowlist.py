import unittest
from v2_registry_source_expansion import extra_sources
class HostAllowlist(unittest.TestCase):
    def test_article_hosts_are_explicit(self):
        for product in ("english","arabic"):
            for row in extra_sources(product):
                self.assertTrue(row["hosts"])
                self.assertTrue(all("." in host for host in row["hosts"]))
    def test_bbc_middle_east_feed_host_retained(self):
        row=next(x for x in extra_sources("english") if x["source_id"]=="en-004")
        self.assertIn("feeds.bbci.co.uk",row["hosts"])
if __name__=="__main__":unittest.main()
