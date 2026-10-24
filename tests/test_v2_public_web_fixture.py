"""Genuine externally viewed publisher snippets retain article/excerpt attribution.

This regression is explicitly NOT an automated live HTTP collection test.
"""
import json
import unittest
from pathlib import Path
from v2_external_capture import compile_web_captures
from v2_evidence import canonical_article_url

ROOT=Path(__file__).resolve().parents[1]

class PublicWebFixtureTests(unittest.TestCase):
    def test_captured_short_excerpts_from_uae_media_office_produce_held_dual_language_event(self):
        fixture=json.loads((ROOT/'fixtures/v2/public_web_excerpt_rehearsal_2026-10-24.json').read_text(encoding='utf8'))
        registry=json.loads((ROOT/'config/v2/source_registry.json').read_text(encoding='utf8'))
        result=compile_web_captures(fixture['captures'],registry=registry,
                                    observed_at=fixture['observed_at'],slot_id=fixture['slot_id'])
        self.assertEqual(result['capture_count'],4)
        self.assertEqual(result['evidence_counters']['events'],3)
        self.assertEqual(result['evidence_counters']['excerpts'],4)
        for stream,source_id,idx in [('english','en-107',0),('arabic','ar-s116',1)]:
            stories=result['products'][stream]['stories']
            self.assertEqual(len(stories),1 if stream=='english' else 3)
            self.assertIn(source_id, [story['source_id'] for story in stories])
            self.assertEqual(next(story['quote'] for story in stories if story['source_id']==source_id),fixture['captures'][idx]['verbatim_excerpt'])
            self.assertEqual(next(story['source_url'] for story in stories if story['source_id']==source_id),canonical_article_url(fixture['captures'][idx]['article_url']))
            self.assertFalse(result['products'][stream]['delivery_authorized'])
        self.assertEqual(result['evidence_counters']['publisher_independence'],'not_verified')
        self.assertEqual(result['capture_receipts'][0]['published_date'],'2026-10-23')
        self.assertEqual(set(result['products']['arabic']['coverage_gaps']).intersection({'gcc','yemen'}),set())
        self.assertEqual(set(story['region'] for story in result['products']['arabic']['stories']),{'gcc','yemen'})
        self.assertIsNone(result['capture_receipts'][0]['published_at'])
        self.assertEqual(result['source_provenance_status'],'web_text_excerpt_observed_not_independently_verified')
        self.assertFalse(result['web_collector_ran'])
        self.assertFalse(result['llm_called'])
        self.assertFalse(result['discord_sent'])

if __name__=='__main__':unittest.main()
