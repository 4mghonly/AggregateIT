"""B32 private static mobile-fixture construction (no browser assertions)."""
import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from v2_b23_compact_mobile import audit_compact_markup
from v2_b32_generate_mobile_fixtures import generate


class MobileFixtureTests(unittest.TestCase):
    def test_bilingual_private_fixture_contract(self):
        with TemporaryDirectory() as tmp:
            result = generate(tmp)
            self.assertEqual(set(result['products']), {'english', 'arabic'})
            for product, info in result['products'].items():
                payload = Path(info['path']).read_bytes()
                self.assertEqual(hashlib.sha256(payload).hexdigest(), info['sha256'])
                html = payload.decode('utf8')
                audit = audit_compact_markup(html, product=product,
                                             expected_stories=info['expected_stories'])
                self.assertTrue(audit['static_checks_passed'])
                self.assertFalse(audit['real_device_verified'])
                self.assertNotIn('https://discord.com/api', html)

    def test_non_empty_output_refused(self):
        with TemporaryDirectory() as tmp:
            generate(tmp)
            with self.assertRaisesRegex(ValueError, 'unsafe_fixture_output_directory'):
                generate(tmp)


if __name__ == '__main__':
    unittest.main()
