"""B46 TDD: exact signed prior journal and no inferred bilingual event mergers."""
import io
import unittest
from v2_evidence import make_article,make_excerpt,make_claim,make_event
from v2_evidence_journal import EvidenceJournal
from v2_evidence_anchor import sign_anchor
from v2_b46_delta_identity import versions_from_signed_journal,review_only_cross_language_pairs
from v2_b46_live_editorial import compile_captured_articles

NOW="2026-10-27T08:00:00+00:00"
SLOT="2026-10-27T12:00:00+04:00"
SECRET=b'k'*32
TEXT=("Officials in Somalia said that regional security representatives met "
      "to consider policy updates and public security communication.")
def story(version=1):
    txt=TEXT if version==1 else TEXT+" A subsequent update was released."
    return {"product":"english","source_id":"en-001",
      "article_url":"https://www.bbc.com/news/articles/c123-example",
      "title":"Somalia security officials outline latest measures",
      "published_at":"2026-10-27T07:00:00+00:00",
      "html_bytes":("<article><p>"+txt+"</p><p>"+txt+"</p></article>").encode("utf8")}
def snapshot(*,url="https://www.bbc.com/news/articles/c123-example",version=1):
    article=make_article(source_id="en-001",url=url,original_text=TEXT if version==1 else TEXT+" A subsequent update was released.",
                         original_language="en",retrieved_at="2026-10-26T18:00:00+00:00",published_at="2026-10-26T17:00:00+00:00")
    excerpt=make_excerpt(article,0,min(70,len(article["original_text"])))
    claim=make_claim(statement=excerpt["literal"],excerpts=[excerpt])
    event=make_event(key="article-"+article["article_id"][4:],claims=[claim])
    journal=EvidenceJournal();buf=io.StringIO()
    for kind,val in (("observe",article),("excerpt",excerpt),("claim",claim),("event",event)):
        journal.append(buf,kind,val,durable=False)
    anchor=sign_anchor(journal.receipt(),secret=SECRET,key_id="test-operator",
                      issued_at="2026-10-26T19:00:00+00:00")
    return {"journal_text":buf.getvalue(),"anchor":anchor,"secret":SECRET,"key_id":"test-operator"}

class DeltaIdentityTests(unittest.TestCase):
    def test_signed_journal_replay_returns_actual_version(self):
        result=versions_from_signed_journal(snapshot(),as_of=NOW)
        self.assertEqual(len(result["versions"]),1)
        self.assertFalse(result["independent_off_host_checkpoint_verified"])
        self.assertEqual(result["baseline_status"],"operator_hmac_verified_not_independently_retained")
    def test_verified_previous_same_article_marks_changed_revision(self):
        res=compile_captured_articles([story(version=2)],as_of=NOW,slot_id=SLOT,
              prior_snapshot=snapshot())
        self.assertEqual(res["products"]["english"]["newsroom"]["stories"][0]["change"],"updated")
        self.assertTrue(res["operator_baseline_hmac_verified"])
        self.assertFalse(res["prior_baseline_off_host_retention_verified"])
        self.assertFalse(res["can_send"])
    def test_signed_absent_article_is_new_attributed_only(self):
        res=compile_captured_articles([story()],as_of=NOW,slot_id=SLOT,
             prior_snapshot=snapshot(url="https://www.bbc.com/news/articles/different"))
        self.assertEqual(res["products"]["english"]["newsroom"]["stories"][0]["change"],"new")
        self.assertFalse(res["source_story_factual_accuracy_verified"])
    def test_tampered_signed_journal_is_rejected(self):
        s=snapshot();s["journal_text"]=s["journal_text"].replace("Somalia","Elsewhere")
        with self.assertRaises(ValueError):
            versions_from_signed_journal(s,as_of=NOW)
    def test_tampered_anchor_and_key_fail_closed(self):
        s=snapshot();s["secret"]=b'x'*32
        with self.assertRaises(ValueError):
            compile_captured_articles([story()],as_of=NOW,slot_id=SLOT,prior_snapshot=s)
    def test_future_anchor_is_refused(self):
        s=snapshot()
        with self.assertRaisesRegex(ValueError,"prior_anchor_outside_bounded_window"):
            versions_from_signed_journal(s,as_of="2026-10-26T18:00:00+00:00")
    def test_untrusted_previous_map_still_cannot_generate_new(self):
        res=compile_captured_articles([story()],as_of=NOW,slot_id=SLOT,previous_versions={})
        self.assertEqual(res["products"]["english"]["newsroom"]["stories"][0]["change"],"unknown_no_baseline")
    def test_region_only_cross_language_pair_is_review_not_merge(self):
        text="مباحثات دبلوماسية في الصومال بشأن العلاقات الإقليمية"
        paragraph="أكد مسؤولون في الصومال عقد مباحثات دبلوماسية مع ممثلين إقليميين لبحث التطورات السياسية ومناقشة بيانات الاجتماع المتعلق بالعلاقات الإقليمية."
        arabic={"product":"arabic","source_id":"ar-s003",
                "article_url":"https://www.aljazeera.net/news/2026/10/27/example",
                "title":text,"published_at":"2026-10-27T07:00:00+00:00",
                "html_bytes":('<div class="wysiwyg--all-content"><p>'+paragraph+
                   '</p><p>'+paragraph+'</p></div>').encode('utf8')}
        res=compile_captured_articles([story(),arabic],as_of=NOW,slot_id=SLOT)
        review=review_only_cross_language_pairs(res["products"])
        self.assertEqual(review["candidate_count"],1)
        self.assertFalse(review["automatic_merge_performed"])
        self.assertEqual(review["candidate_pairs"][0]["semantic_event_identity"],"UNVERIFIED")
        self.assertNotEqual(review["candidate_pairs"][0]["english_event_id"],review["candidate_pairs"][0]["arabic_event_id"])
    def test_fake_products_cannot_be_merged(self):
        with self.assertRaises(ValueError):
            review_only_cross_language_pairs({"english":{},"arabic":{}})
if __name__=="__main__":unittest.main()
