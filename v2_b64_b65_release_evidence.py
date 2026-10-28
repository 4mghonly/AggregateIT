"""B64/B65 isolated evidence qualification. Never authorizes production release."""
from __future__ import annotations

AUDIT_RUN = 40659308048
AUDIT_COMMIT = "6e6094d400a82787aa5970c4d985a16ec02158d3"
AUDIT_STEPS = (
    "Run pip install aiohttp feedparser requests",
    "Run python audit.py",
    "Run actions/upload-artifact@v6",
)
SOMALIA_CANDIDATES = (
    {"publisher": "Shabelle Media", "language": "so", "enabled": False},
    {"publisher": "Somali Dispatch", "language": "en", "enabled": False},
)

def verify_audit_receipt(receipt):
    """Require independent run metadata, correct commit and successful steps."""
    if not isinstance(receipt, dict):
        return False
    if receipt.get("run_id") != AUDIT_RUN or receipt.get("head_sha") != AUDIT_COMMIT:
        return False
    if receipt.get("branch") != "main" or receipt.get("conclusion") != "success":
        return False
    steps = receipt.get("steps")
    if not isinstance(steps, list):
        return False
    successful = {s.get("name") for s in steps
                  if isinstance(s, dict) and s.get("conclusion") == "success"}
    return all(name in successful for name in AUDIT_STEPS)

def reconcile_release_checks(existing_checks, audit_receipt):
    """Clear audit dependency only; never infer any other acceptance."""
    if not isinstance(existing_checks, dict) or not existing_checks:
        raise ValueError("missing_release_checks")
    checks = dict(existing_checks)
    if "production_source_audit_dependency_green" not in checks:
        raise ValueError("missing_audit_gate")
    checks["production_source_audit_dependency_green"] = verify_audit_receipt(audit_receipt)
    return {"checks": checks,
            "open_release_blocks": [key for key, passed in checks.items() if passed is not True],
            "release_status": "HOLD", "can_release": False}

def qualify_somalia_candidates(candidates, observations=()):
    """Record disabled independent publishers; do not assert live coverage."""
    if not isinstance(candidates, (list, tuple)) or len(candidates) < 2:
        raise ValueError("insufficient_candidates")
    names = set()
    for candidate in candidates:
        if not isinstance(candidate, dict) or candidate.get("enabled") is not False:
            raise ValueError("candidate_must_remain_disabled")
        name = candidate.get("publisher")
        if not isinstance(name, str) or not name.strip() or name.casefold() in names:
            raise ValueError("duplicate_or_missing_publisher")
        if candidate.get("language") not in ("so", "en", "ar"):
            raise ValueError("invalid_source_language")
        names.add(name.casefold())
    return {"candidates": list(candidates), "distinct_publishers": len(names),
            "live_observations": len(observations),
            "real_arabic_translation_verified": False,
            "production_coverage_accepted": False,
            "activation_allowed": False}
