"""One unsendable Discord manifest for each weekly report PDF."""
import unittest
from v2_weekly_discord import bundle_weekly_pdf

REPORT = {
    'schema': 'aggregateit-v2-weekly-rollup/1',
    'product': 'english', 'as_of': '2026-10-24T06:00:00+04:00',
    'window_days': 7, 'unique_events': 2, 'days_with_snapshots': 3,
    'regions_covered':['gcc'], 'regions_uncovered':[],
    'market_changes':[], 'delivery_authorized':False,
}
PDF = b'%PDF-1.4\n% synthetic offline verification fixture\n'


class WeeklyDiscordTests(unittest.TestCase):
    def test_english_has_one_unsendable_message_and_correct_digest(self):
        result=bundle_weekly_pdf(REPORT,PDF)
        self.assertEqual(result['message_count'],1)
        self.assertEqual(result['destination_key'],'discord_webhook')
        self.assertEqual(len(result['attachments']),1)
        self.assertFalse(result['can_send'])
        self.assertEqual(result['format'],'pdf')

    def test_arabic_uses_separate_channel_without_market_material(self):
        rpt={**REPORT,'product':'arabic','regions_uncovered':['somalia']}
        result=bundle_weekly_pdf(rpt,PDF)
        self.assertEqual(result['destination_key'],'discord_webhook_arabic')
        self.assertEqual(result['coverage_gaps'],['somalia'])
        self.assertNotIn('Markets',result['content'])

    def test_arabic_rejects_finance_records(self):
        rpt={**REPORT,'product':'arabic','market_changes':[{'instrument':'WTI'}]}
        with self.assertRaises(ValueError):bundle_weekly_pdf(rpt,PDF)

    def test_live_report_claim_refused(self):
        rpt={**REPORT,'delivery_authorized':True}
        with self.assertRaises(ValueError):bundle_weekly_pdf(rpt,PDF)

    def test_invalid_pdf_signature_refused(self):
        with self.assertRaises(ValueError):bundle_weekly_pdf(REPORT,b'<html>wrong</html>')


if __name__=='__main__': unittest.main()
