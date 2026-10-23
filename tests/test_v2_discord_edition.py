"""Contract tests: Discord-first packaging never sends a webhook."""
import unittest
from hashlib import sha256
from v2_discord_edition import prepare_discord_edition

PNG=b'\x89PNG\r\n\x1a\n' + b'synthetic-bytes-for-contract-test'
SLOT='2026-10-24T06:00:00+04:00'

def pages(n,format='png'):
    body=PNG if format=='png' else b'%PDF-1.4\nsynthetic'
    return [{'filename':f'page-{i}.{format}','content':body,
             'sha256':sha256(body).hexdigest()} for i in range(n)]

class DiscordContractTests(unittest.TestCase):
    def bundle(self, *, product='english',cadence='daily',attachments=None,topics=None,**kw):
        if attachments is None:attachments=pages(2 if product=='english' else 3)
        if topics is None:topics=['geopolitics','markets'] if product=='english' else ['geopolitics','security']
        return prepare_discord_edition(product=product,cadence=cadence,slot_id=SLOT,pages=attachments,
            headline='Synthetic briefing',summary=['Fictional news development'],included_topics=topics,
            regions=['gcc','iran'],coverage_gaps=['somalia'],critical_review='insufficient_evidence',
            synthetic=True,**kw)
    def test_english_combines_markets_and_geopolitics(self):
        x=self.bundle()
        self.assertEqual(x['message_count'],1)
        self.assertEqual(x['destination_key'],'discord_webhook')
        self.assertEqual(len(x['attachments']),2)
        self.assertIn('Markets + geopolitics',x['content'])
        self.assertFalse(x['can_send'])
    def test_arabic_route_keeps_geopolitics_only(self):
        x=self.bundle(product='arabic')
        self.assertEqual(x['destination_key'],'discord_webhook_arabic')
        self.assertIn('نواقص التغطية',x['content'])
    def test_arabic_financial_topic_rejected(self):
        with self.assertRaisesRegex(ValueError,'arabic_financial_topic_forbidden'):
            self.bundle(product='arabic',topics=['geopolitics','markets'])
    def test_english_missing_market_is_rejected(self):
        with self.assertRaises(ValueError):self.bundle(topics=['geopolitics'])
    def test_no_cross_channel_or_unsupported_attachment_count(self):
        with self.assertRaises(ValueError):self.bundle(attachments=pages(3))
        with self.assertRaises(ValueError):self.bundle(cadence='weekly',attachments=pages(11))
    def test_weekly_pdf_is_supported_without_sender(self):
        x=self.bundle(cadence='weekly',attachments=pages(1,'pdf'))
        self.assertEqual(x['format'],'pdf')
        self.assertEqual(x['message_count'],1)
    def test_checksum_mismatch_rejected(self):
        p=pages(2);p[0]['sha256']='0'*64
        with self.assertRaises(ValueError):self.bundle(attachments=p)
    def test_mixed_format_rejected(self):
        p=pages(1)+pages(1,'pdf')
        p[1]['filename']='other.pdf'
        with self.assertRaises(ValueError):self.bundle(attachments=p)
    def test_mention_markup_neutralized(self):
        x=prepare_discord_edition(product='english',cadence='daily',slot_id=SLOT,
            pages=pages(2),headline='@everyone <@123> alert',summary=[],
            included_topics=['markets','geopolitics'],regions=['gcc'],synthetic=True)
        self.assertNotIn('@everyone',x['content'])
        self.assertNotIn('<@123>',x['content'])
    def test_non_synthetic_and_naive_slot_refused(self):
        with self.assertRaises(ValueError):
            prepare_discord_edition(product='english',cadence='daily',slot_id=SLOT,
                pages=pages(2),headline='Test',summary=[],
                included_topics=['markets','geopolitics'],regions=[],synthetic=False)
        with self.assertRaises(ValueError):
            prepare_discord_edition(product='english',cadence='daily',slot_id='2026-10-24T06:00:00',
                pages=pages(2),headline='Test',summary=[],
                included_topics=['markets','geopolitics'],regions=[],synthetic=True)

if __name__=='__main__':unittest.main()
