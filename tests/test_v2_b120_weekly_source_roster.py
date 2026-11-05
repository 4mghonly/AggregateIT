"""B120: real-day publisher-source manifests, not synthetic weekly publications."""
import copy
import json
import unittest
from datetime import date, timedelta
from v2_b120_weekly_source_roster import make_daily_source_roster, seven_day_roster, manifest_sha256

def edition(when):
    def product(lang):
        return {'editorial_plan': {'schema':'aggregateit-editorial-plan/1',
            'product':lang,'language':{'english':'en','arabic':'ar'}[lang],
            'as_of':when,'delivery_authorized':False,
            'items':[{'event_id':'ev-'+lang,'version_id':'ver-'+lang,
                'region':'somalia','topic':'security','priority':7,
                'evidence':{'source_id':'src-'+lang,'excerpt_id':'ex-'+lang,
                    'source_url':'https://www.example.org/'+lang,
                    'quote':'Proprietary original text not for release',
                    'original_language':{'english':'en','arabic':'ar'}[lang]}}]}}
    return {'schema':'aggregateit-v2-b46-article-editorial/1','can_send':False,
            'products':{'english':product('english'),'arabic':product('arabic')}}

def daily(day,run):
    at=f'{day}T07:00:00+00:00'
    return make_daily_source_roster(edition(at),observed_at=at,
        run_id=str(run),head_sha='a'*40, capture_sha256='b'*64)

def metadata(row):
    return {'id':int(row['github_run_id']),'head_sha':row['head_sha'],
            'head_branch':'rebuild/aggregateit-v2',
            'path':'.github/workflows/v2-b80-b83-live-acceptance.yml',
            'status':'completed','conclusion':'success','event':'workflow_dispatch',
            'run_started_at':row['observed_at']}

class WeeklyRosterTests(unittest.TestCase):
    def test_no_publisher_quote_or_headline_is_persisted(self):
        row=daily('2026-11-06',601)
        raw=json.dumps(row)
        self.assertNotIn('Proprietary original text',raw)
        self.assertNotIn('"quote"',raw)
        self.assertEqual(row['products']['english']['story_count'],1)
        self.assertFalse(row['can_release'])
        self.assertEqual(row['manifest_sha256'],manifest_sha256(row))

    def test_real_runner_emits_roster_only_with_github_context(self):
        from unittest.mock import patch
        from test_v2_replacement_pipeline import run, snapshots, fake_fetch, AT
        with patch.dict('os.environ', {'GITHUB_RUN_ID':'999321','GITHUB_SHA':'a'*40}):
            output=run(rss_snapshots=snapshots(),observed_at=AT,fetch=fake_fetch,
                       compare_same_capture=True,market_snapshot={})
        row=output['b120_weekly_source_roster']
        self.assertEqual(row['github_run_id'],'999321')
        self.assertEqual(row['products']['english']['story_count'],1)
        self.assertEqual(row['products']['arabic']['story_count'],1)
        self.assertNotIn('Somalia security officials',json.dumps(row))
        self.assertFalse(row['can_release'])

    def test_stale_or_forged_manifest_fails_closed(self):
        row=daily('2026-11-06',601)
        row['products']['english']['stories'][0]['source_id']='modified'
        with self.assertRaisesRegex(ValueError,'manifest_digest'):
            seven_day_roster([row],[metadata(row)],today=date(2026,11,6),expected_sha='a'*40)

    def test_missing_days_never_backfill(self):
        row=daily('2026-11-06',601)
        out=seven_day_roster([row],[metadata(row)],today=date(2026,11,6),expected_sha='a'*40)
        self.assertEqual(out['status'],'HOLD_MISSING_GENUINE_DAYS')
        self.assertEqual(out['genuine_distinct_days'],1)
        self.assertFalse(out['complete_seven_day_source_roster'])
        self.assertFalse(out['can_release'])

    def test_duplicate_day_not_cherry_picked(self):
        a=daily('2026-11-06',601)
        b=daily('2026-11-06',602)
        out=seven_day_roster([a,b],[metadata(a),metadata(b)],today=date(2026,11,6),expected_sha='a'*40)
        self.assertEqual(out['status'],'HOLD_AMBIGUOUS_DATE')
        self.assertEqual(out['genuine_distinct_days'],0)

    def test_real_run_metadata_and_single_sha_needed(self):
        base=date(2026,11,6)
        rows=[daily((base-timedelta(days=6-i)).isoformat(),601+i) for i in range(7)]
        out=seven_day_roster(rows,[metadata(r) for r in rows],
                             today=base,expected_sha='a'*40)
        self.assertEqual(out['status'],'COMPLETE_ATTRIBUTED_SOURCE_ROSTER_NO_POST')
        self.assertEqual(out['genuine_distinct_days'],7)
        self.assertTrue(out['complete_seven_day_source_roster'])
        self.assertFalse(out['full_editorial_model_visual_delivery_parity'])
        rows[-1]['head_sha']='c'*40
        with self.assertRaisesRegex(ValueError,'manifest_digest'):
            seven_day_roster(rows,[metadata(r) for r in rows],today=base,expected_sha='a'*40)

if __name__=='__main__':
    unittest.main()
