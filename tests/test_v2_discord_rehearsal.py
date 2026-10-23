"""Mock boundary tests for the no-send bilingual renderer bridge."""
import sys
import types
import unittest
from unittest.mock import patch
from hashlib import sha256
from v2_discord_rehearsal import rehearse_discord_bundle

PNG=b'\x89PNG\r\n\x1a\n' + b'synthetic content'
SLOT='2026-10-24T06:00:00+04:00'

class DiscordRendererBridgeTests(unittest.TestCase):
    def stub(self,product):
        name='v2_english_application_rehearsal' if product=='english' else 'v2_arabic_application_rehearsal'
        module=types.ModuleType(name)
        fixture={'slot_id':SLOT,'documents':[{'region':'gcc'}]}
        result={'synthetic':True,'discord_sent':False,
                'source_ids':['synthetic-1'],'evidence_receipt':{'seq':1},
                'pages':[{'page_number':i,'png':PNG,'sha256':sha256(PNG).hexdigest()}
                         for i in range(1,(3 if product=='english' else 4))]}
        if product=='english':
            module.synthetic_fixture=lambda:fixture
            module.rehearse_english=lambda fixture,registry:result
        else:
            module.arabic_synthetic_fixture=lambda:fixture
            module.rehearse_arabic=lambda fixture,registry:result
        return name,module
    def test_either_product_delivers_only_one_unsendable_manifest(self):
        for product,number in (('english',2),('arabic',3)):
            name,module=self.stub(product)
            with patch.dict(sys.modules,{name:module}):
                report=rehearse_discord_bundle(product=product,registry={'mock':True})
            self.assertEqual(report['rendered_page_count'],number)
            self.assertEqual(report['manifest']['message_count'],1)
            self.assertEqual(len(report['manifest']['attachments']),number)
            self.assertFalse(report['discord_sent'])
            self.assertFalse(report['manifest']['can_send'])
    def test_unknown_product_refused(self):
        with self.assertRaises(ValueError):
            rehearse_discord_bundle(product='other',registry={})
    def test_upstream_claimed_send_is_not_admitted(self):
        name,module=self.stub('english')
        module.rehearse_english=lambda f,r:{'synthetic':True,'discord_sent':True,'pages':[]}
        with patch.dict(sys.modules,{name:module}):
            with self.assertRaises(ValueError):
                rehearse_discord_bundle(product='english',registry={})

if __name__=='__main__':unittest.main()
