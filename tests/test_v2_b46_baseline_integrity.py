"""B46 stage-2 canonical replay and untrusted baseline guard.

TDD target: no caller-supplied previous-version map can generate a false
'new since previous' claim without independently authenticated prior state.
"""
import unittest
from v2_b46_live_editorial import compile_captured_articles
NOW="2026-10-27T08:00:00+00:00"
SLOT="2026-10-27T12:00:00+04:00"

def en():
    para=("Officials in Somalia said their security teams met with regional representatives "
          "to discuss the security situation and review the public statements about new measures.")
    return {"product":"english","source_id":"en-001",
            "article_url":"https://www.bbc.com/news/articles/c123-example",
            "title":"Somalia security officials outline latest measures",
            "published_at":"2026-10-27T07:00:00+00:00",
            "html_bytes":("<article><p>"+para+"</p><p>"+para+"</p></article>").encode("utf8")}

class BaselineAndUrlTests(unittest.TestCase):
    def test_untrusted_previously_seen_versions_never_promote_new_status(self):
        result=compile_captured_articles([en()],as_of=NOW,slot_id=SLOT,
                                         previous_versions={'evt_untrusted':'v0'})
        self.assertEqual(result['products']['english']['newsroom']['stories'][0]['change'],
                         'unknown_no_baseline')
        self.assertTrue(result['unattested_previous_versions_ignored'])
        self.assertFalse(result['prior_baseline_authenticated'])
    def test_tracking_duplicate_is_held_under_article_identity(self):
        original=en();mirror=en()
        mirror['article_url']+='?utm_source=internal'
        result=compile_captured_articles([original,mirror],as_of=NOW,slot_id=SLOT)
        self.assertEqual(result['admitted_articles'],1)
        self.assertEqual(result['held_reasons']['repeated_canonical_article_url'],1)
        self.assertFalse(result['can_send'])
if __name__=='__main__':unittest.main()
