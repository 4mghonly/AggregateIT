"""B41 static real production baseline contract and controlled HOLD."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from v2_b41_production_preflight import inspect_workflows,FILES,V1_PARSERS,EXPECTED_CRONS,EXPECTED_NAMES

def build(root,*,mutate_main=True):
    for rel in FILES:
        path=root/rel;path.parent.mkdir(parents=True,exist_ok=True)
        name=path.name
        crons=sorted(EXPECTED_CRONS.get(name,set()))
        name_str=EXPECTED_NAMES.get(name,name)
        schedule='\n'.join('    - cron: "'+v+'"' for v in crons)
        if not schedule:schedule='    - cron: "0 0 * * *"'
        extra='    run: git push origin HEAD:main\n' if mutate_main and name=='arabic-source-audit.yml' else ''
        path.write_text('name: '+name_str+'\non:\n  schedule:\n'+schedule+'\n  workflow_dispatch:\njobs:\n  check:\n    runs-on: ubuntu-latest\n'+extra)
    for rel in V1_PARSERS:
        p=root/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('pass\n')
class ProductionPreflightTests(unittest.TestCase):
    def test_pinned_baseline_revision_and_mutating_source_audit_flagged(self):
        with tempfile.TemporaryDirectory() as b,tempfile.TemporaryDirectory() as c:
            build(Path(b));build(Path(c))
            def rev(path):return 'a'*40 if path==Path(b) else 'b'*40
            with patch('v2_b41_production_preflight._revision',side_effect=rev):
                x=inspect_workflows(baseline_root=Path(b),candidate_root=Path(c),main_sha='a'*40)
        self.assertEqual(x['status'],'HOLD_PRODUCTION_CANARY')
        self.assertTrue(x['main_auto_write_workflow_present'])
        self.assertIn('production_audit_can_advance_main_during_canary',x['preflight_findings'])
        self.assertFalse(x['can_release'])
    def test_unexpected_main_revision_refused(self):
        with tempfile.TemporaryDirectory() as b,tempfile.TemporaryDirectory() as c:
            build(Path(b));build(Path(c))
            with patch('v2_b41_production_preflight._revision',return_value='a'*40):
                with self.assertRaisesRegex(ValueError,'baseline_revision_mismatch'):
                    inspect_workflows(baseline_root=Path(b),candidate_root=Path(c),main_sha='b'*40)
    def test_modified_v1_parser_is_reported(self):
        with tempfile.TemporaryDirectory() as b,tempfile.TemporaryDirectory() as c:
            build(Path(b),mutate_main=False);build(Path(c),mutate_main=False)
            (Path(c)/'main.py').write_text('changed')
            with patch('v2_b41_production_preflight._revision',side_effect=['a'*40,'b'*40]):
                x=inspect_workflows(baseline_root=Path(b),candidate_root=Path(c))
        self.assertIn('legacy_parser_changed_main.py',x['preflight_findings'])
    def test_changed_schedule_is_flagged(self):
        with tempfile.TemporaryDirectory() as b,tempfile.TemporaryDirectory() as c:
            build(Path(b));build(Path(c))
            p=Path(b)/'.github/workflows/slide.yml'
            p.write_text(p.read_text().replace('30 11 * * *','59 23 * * *'))
            with patch('v2_b41_production_preflight._revision',side_effect=['a'*40,'b'*40]):
                x=inspect_workflows(baseline_root=Path(b),candidate_root=Path(c))
        self.assertIn('schedule_mismatch_slide.yml',x['preflight_findings'])
    def test_absent_workflow_refused(self):
        with tempfile.TemporaryDirectory() as b,tempfile.TemporaryDirectory() as c:
            build(Path(b));build(Path(c))
            (Path(b)/FILES[0]).unlink()
            with patch('v2_b41_production_preflight._revision',side_effect=['a'*40,'b'*40']):
                with self.assertRaisesRegex(ValueError,'missing_production_workflow'):
                    inspect_workflows(baseline_root=Path(b),candidate_root=Path(c))
if __name__=='__main__':unittest.main()
