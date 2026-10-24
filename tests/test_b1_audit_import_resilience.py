"""Source audit must import lazily even if an RSS parsing dependency is absent."""
import os
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]


class AuditImportResilienceTests(unittest.TestCase):
    def test_audit_can_be_imported_in_plain_repository_environment(self):
        # This intentionally excludes the import-only development shims.
        env = dict(os.environ)
        env['PYTHONPATH'] = str(ROOT)
        result = subprocess.run(
            [sys.executable, '-B', '-c', 'import audit; print("AUDIT_IMPORT_OK")'],
            cwd=str(ROOT), env=env, text=True, capture_output=True, timeout=10,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('AUDIT_IMPORT_OK', result.stdout)


if __name__ == '__main__':
    unittest.main()
