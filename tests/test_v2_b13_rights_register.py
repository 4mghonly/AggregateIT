"""The B13 rights register is a review/HOLD document, not a legal clearance."""
import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
REGISTER=ROOT/'config/v2/b13_regional_rights_review_2026-10-24.json'
REGIONS=frozenset(('gcc','oman','iran','turkey','iraq','yemen','sudan','sahel',
                   'north_africa','egypt','pakistan','afghanistan','somalia',
                   'horn','palestine_israel','levant','jordan'))

class RegionalRightsRegisterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc=json.loads(REGISTER.read_text(encoding='utf8'))
    def test_all_regions_have_at_least_one_source_candidate(self):
        self.assertEqual({r['region'] for r in self.doc['coverage']},REGIONS)
        self.assertTrue(all(r['sources'] for r in self.doc['coverage']))
    def test_no_source_claims_commercial_permission_without_evidence(self):
        self.assertFalse(self.doc['release_authorized'])
        self.assertFalse(self.doc['publication_rights_verified'])
        for region in self.doc['coverage']:
            self.assertFalse(region['editorial_coverage_verified'])
            self.assertFalse(region['original_article_republication_allowed'])
            for source in region['sources']:
                self.assertIsNone(source['commercial_reuse_permission_document'])
                self.assertEqual(source['rights_decision'],'hold_until_document_specific_rights_or_permission_confirmed')
    def test_known_restrictions_are_explicit(self):
        precedents={r['publisher']:r for r in self.doc['publisher_rights_precedents']}
        for name in ('BBC News','Al Jazeera','Reuters','WAM'):
            self.assertEqual(precedents[name]['status'],'explicit_permission_required')
            self.assertTrue(precedents[name]['url'].startswith('https://'))
    def test_language_candidates_do_not_claim_native_arabic_for_farsi_somali(self):
        source={r['source_id']:r for region in self.doc['coverage'] for r in region['sources']}
        self.assertEqual(source['ar-s019']['original_language_candidate'],'fa')
        self.assertEqual(source['ar-s056']['original_language_candidate'],'so')
        self.assertEqual(source['ar-s055']['original_language_candidate'],'fa')

if __name__=='__main__': unittest.main()
