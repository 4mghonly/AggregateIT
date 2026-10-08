"""Read-only overdue-run check. Never dispatch production or post to Discord."""
import json
import os
from pathlib import Path
import requests
from runtime_health import overdue_runs


def main():
    repo=os.getenv("GITHUB_REPOSITORY","4mghonly/AggregateIT")
    headers={"Accept":"application/vnd.github+json"}
    if os.getenv("GITHUB_TOKEN"): headers["Authorization"]="Bearer "+os.environ["GITHUB_TOKEN"]
    response=requests.get(f"https://api.github.com/repos/{repo}/actions/runs",
                          params={"branch":"main","per_page":100},headers=headers,timeout=(5,20))
    response.raise_for_status()
    issues=overdue_runs(response.json().get("workflow_runs",[]))
    out=Path("reports/operations_health.json");out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps({"status":"degraded" if issues else "ok","issues":issues},indent=2))
    for issue in issues: print("::error::"+issue)
    return int(bool(issues))


if __name__=="__main__": raise SystemExit(main())
