"""B12: prevent fresh lxml/justext runtime dependency failures."""
import subprocess
import sys
import unittest


class ProductionPythonDeps(unittest.TestCase):
    def test_html_clean_and_trafilatura_resolve_after_requirements_install(self):
        run=subprocess.run(
            [sys.executable,'-B','-c',
             'from lxml.html.clean import Cleaner; import trafilatura; print("IMPORT_OK")'],
            text=True,capture_output=True,timeout=18)
        self.assertEqual(run.returncode,0,run.stderr[-2000:])
        self.assertIn('IMPORT_OK',run.stdout)


if __name__=='__main__':unittest.main()
