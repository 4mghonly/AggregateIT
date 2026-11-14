import ast,unittest
from pathlib import Path
P=Path(__file__).resolve().parents[1]/"v2_b46_live_editorial_runner.py"
class RunnerWiring(unittest.TestCase):
 def test_runner_accepts_provider(self):
  tree=ast.parse(P.read_text())
  run=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="run")
  self.assertIn("analysis_provider",[a.arg for a in run.args.kwonlyargs])
 def test_compiler_receives_provider(self):
  self.assertIn("analysis_provider=analysis_provider",P.read_text())
 def test_cli_opt_in_model_endpoint(self):
  text=P.read_text()
  self.assertIn("--analysis-model",text)
  self.assertIn("--analysis-base-url",text)
  self.assertIn("AGGREGATEIT_ANALYSIS_API_KEY",text)
if __name__=="__main__":unittest.main()
