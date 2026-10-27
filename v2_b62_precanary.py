"""B62 immutable pre-canary decision pack: no production mutations or auto-approval."""
from __future__ import annotations
from v2_b58_model_release_gate import assess_selection

RELEASE_ITEMS=(
 "b59_actual_publisher_semantic_quality",
 "b60_same_snapshot_v2_page_editorial_visual_qa",
 "b61_signed_seven_real_days_per_language",
 "b49_same_slot_full_v1_v2_model_editorial_render_delivery",
 "production_source_audit_dependency_green",
 "somalia_distinct_compatible_sources_at_least_two",
 "primary_and_fallback_live_route_health",
 "independent_discord_client_receipts",
 "authorized_production_canary"
)
def evaluate_precanary(model_config, *,b59,b60,b61, attestation=None):
    model=assess_selection(model_config)
    if not all(isinstance(x,dict) for x in (b59,b60,b61)):
        raise ValueError("missing_batch_evidence")
    if (b59.get("schema")!="aggregateit-v2-b59-fixture-contract/1"
        or b60.get("schema")!="aggregateit-v2-b60-visual-acceptance/1"
        or b61.get("schema")!="aggregateit-v2-b61-7day-lineage/1"):
        raise ValueError("untrusted_batch_receipts")
    if any(x.get("can_release") is not False for x in (b59,b60,b61)):
        raise ValueError("evidence_contains_send_authority")
    if attestation is not None:
        if not isinstance(attestation,dict):raise ValueError("invalid_operator_claims")
        if any(attestation.get(x) is True for x in RELEASE_ITEMS):
            # Never accept caller booleans as evidence of production authority.
            raise ValueError("self_asserted_live_acceptance_not_independent_evidence")
    return {"schema":"aggregateit-v2-b62-precanary/1",
            "model_primary_staged":model["model_primary_staged"],
            "model_fallback_staged":model["model_fallback_staged"],
            "model_configuration_enabled":False,
            "checks":{key:False for key in RELEASE_ITEMS},
            "open_release_blocks":list(RELEASE_ITEMS),
            "fixture_translation_contract_passed":b59["checks_passed"],
            "geometry_violations":(b60["candidate_geometry"] or {}).get("violations",[]),
            "weekly_held_days":b61["observed_days"],
            "model_approved_budget_usd":model_config["budget"]["approved_usd"],
            "model_reported_spent_usd":model_config["budget"]["spent_reported_b55_b56_b57_usd"],
            "new_paid_calls":0,
            "legal_review_out_of_scope":True,
            "production_main_modified":False,
            "production_secrets_modified":False,
            "production_db_modified":False,
            "discord_sent":False,
            "automated_canary":False,
            "release_status":"HOLD","can_release":False}
