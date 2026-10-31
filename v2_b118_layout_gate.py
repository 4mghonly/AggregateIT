"""Non-publishing page allocation preflight; does not claim visual validation."""
def layout_preflight(items, *, language="ar"):
    if language not in ("ar","en") or not isinstance(items,list):
        raise ValueError("invalid_layout_input")
    if any(not isinstance(x,dict) for x in items):
        raise ValueError("invalid_layout_item")
    if language=="en":
        return {"pages":[{"section":"headlines","item_count":min(6,len(items))},
                         {"section":"analysis","item_count":0}],
                "within_page_budget":len(items)<=6}
    uae=[x for x in items if x.get("subject_country")=="AE"]
    other=[x for x in items if x.get("subject_country")!="AE"]
    first=(uae[:2]+other[:max(0,4-min(2,len(uae)))])[:4]
    selected_ids={id(x) for x in first}
    second=[x for x in items if id(x) not in selected_ids][:5]
    return {"pages":[{"section":"uae_and_priority","item_count":len(first)},
                     {"section":"regional_reporting","item_count":len(second)},
                     {"section":"analytics_and_watch","item_count":0}],
            "uae_evidence_present":bool(uae),
            "within_page_budget":len(items)<=9,
            "overflow_items":max(0,len(items)-9),
            "visual_clipping_verified":False}
