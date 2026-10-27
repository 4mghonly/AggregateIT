"""B36 strict shared-source-byte and fixed-metric provenance contract."""
import copy
import unittest
from v2_b36_same_snapshot_scorecard import compare_same_snapshot_metrics

SLOT_START='2026-10-26T06:00:00+04:00'
SLOT_END='2026-10-26T12:00:00+04:00'

def run(rev):
    return dict(product='english',window_start=SLOT_START,window_end=SLOT_END,
                code_revision=rev,delivery_status='not_attempted',
                metrics=dict(sources_attempted=1,sources_usable=1,events_selected=1,
                             items_cited=1,items_rendered=1,translation_attempted=0,
                             translation_succeeded=0,layout_omissions=0,clipped_items=0),
                region_counts={'gcc':1})

def original():
    return [{'source_id':'bbc','source_revision':'capture-1',
             'source_bytes':b'<rss><item>synthetic source data</item></rss>'}]

class SnapshotScorecardTests(unittest.TestCase):
    def test_matching_source_bytes_compare_only_offline(self):
        a=original(); b=copy.deepcopy(a)
        result=compare_same_snapshot_metrics(run('a'*40),run('b'*40),a,b)
        self.assertTrue(result['exact_input_bytes_compared'])
        self.assertEqual(result['status'],'OFFLINE_SAME_INPUT_METRIC_COMPARISON')
        self.assertFalse(result['metric_values_authenticated'])
        self.assertFalse(result['full_edition_delivery_comparable'])
        self.assertFalse(result['delivery_authorized'])
        self.assertNotIn('synthetic source data',str(result))

    def test_different_raw_bytes_hold_without_deltas(self):
        bad=original();bad[0]['source_bytes']=b'<rss>changed</rss>'
        result=compare_same_snapshot_metrics(run('a'*40),run('b'*40),original(),bad)
        self.assertEqual(result['status'],'HOLD')
        self.assertEqual(result['reason'],'different_source_bytes_or_roster')
        self.assertNotIn('scorecard',result)

    def test_different_capture_revision_hold(self):
        bad=original();bad[0]['source_revision']='capture-2'
        self.assertEqual(compare_same_snapshot_metrics(run('a'*40),run('b'*40),original(),bad)['status'],'HOLD')

    def test_different_window_hold(self):
        candidate=run('b'*40);candidate['window_end']='2026-10-26T18:00:00+04:00'
        self.assertEqual(compare_same_snapshot_metrics(run('a'*40),candidate,original(),original())['status'],'HOLD')

    def test_same_revision_hold(self):
        self.assertEqual(compare_same_snapshot_metrics(run('a'*40),run('a'*40),original(),original())['status'],'HOLD')

    def test_empty_sources_rejected(self):
        with self.assertRaisesRegex(ValueError,'invalid_replay_items'):
            compare_same_snapshot_metrics(run('a'*40),run('b'*40),[],[])

    def test_metric_count_contradiction_rejected(self):
        bad=run('b'*40);bad['metrics']['items_rendered']=2
        with self.assertRaises(ValueError):
            compare_same_snapshot_metrics(run('a'*40),bad,original(),original())


if __name__=='__main__': unittest.main()
