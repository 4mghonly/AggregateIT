"""B46 stage 4: actual TradingView scanner *observation*, no market publication.

Calls existing V2 scanner contract, quarantines all values without exchange-side
time, independent quote corroboration, or verified distribution rights.
No LLM analysis, financial claim generation, trade advice or Discord send.
"""
from __future__ import annotations
from v2_live_scanner_contract import classify_scanner_response
MACRO = ("TVC:DXY", "COMEX:GC1!", "NYMEX:CL1!")

def assess_market_observation(response, *, observed_at, requested=None):
    symbols=list(requested or MACRO)
    if len(symbols)>3 or not set(symbols).issubset(MACRO):
        raise ValueError("unapproved_b46_market_universe")
    result=classify_scanner_response(response,requested=symbols,kind="macro",observed_at=observed_at)
    if result["publisher_timestamp_verified"] or result["price_accuracy_verified"] or result["publishable"]:
        raise ValueError("unapproved_market_provenance_elevation")
    observations=result["observations"]
    nonnull=sum(row.get("close") is not None for row in observations)
    return {"schema":"aggregateit-v2-b46-macro-diagnostic/1",
            "provider":"tradingview_scanner",
            "requested":symbols,"received_symbols":[r["symbol"] for r in observations],
            "missing_symbols":result["missing_symbols"],"close_measurements_available":nonnull,
            "received_count":len(observations),"scanner_response_status":result["status"],
            "request_observed_at":result["observed_at"],
            "exchange_quote_timestamp_verified":False,
            "independent_market_price_verified":False,
            "rights_for_republication_verified":False,
            "market_data_can_enter_edition":False,
            "can_release":False,"discord_sent":False}

def audit_critic_abstention(products):
    if not isinstance(products,dict) or set(products)!={"english","arabic"}:
        raise ValueError("invalid_products")
    result={}
    for product in ("english","arabic"):
        report=products[product]
        if report.get("no_publication_authority") is not True:
            raise ValueError("untrusted_critical_review")
        critic=report.get("critique")
        if not isinstance(critic,dict) or critic.get("schema")!="aggregateit-naysayer-report/1":
            raise ValueError("invalid_naysayer_schema")
        sections=critic.get("sections")
        if not isinstance(sections,list) or len(sections)!=1:
            raise ValueError("incorrect_daily_naysayer_count")
        section=sections[0]
        if (section.get("review_status") not in ("withheld","insufficient_evidence")
            or section.get("cited_evidence") or section.get("factual_accuracy_verified") is not False
            or section.get("delivery_authorized") is not False):
            raise ValueError("unsupported_substantive_critic")
        if report.get("newsroom",{}).get("naysayer_status")!=section["review_status"]:
            raise ValueError("critic_and_compiler_disagree")
        result[product]={"review_status":section["review_status"],
                        "material_evidence_available":False,
                        "independent_operator_challenge_verified":False}
    return {"schema":"aggregateit-v2-b46-critic-held/1",
            "products":result,"live_analysis_generated":False,
            "editorial_critique_publishable":False,"can_release":False}
