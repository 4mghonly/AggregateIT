"""B60 original visual defect register + strict geometry checks, no false V2 clearance."""
from __future__ import annotations
from hashlib import sha256

KNOWN_DEFECTS={
 "en_title_lead_mismatch":"English original headline unrelated to nearby market lead",
 "en_chart_edge_clipping":"English original chart/axis labels clipped or crowded",
 "ar_uae_priority_empty":"Arabic UAE-priority content absent despite prominent slot",
 "ar_font_density":"Arabic original small, dense typography",
 "ar_repeated_panels":"Arabic original repeats stories across category panels"
}
def inspect_layout_geometry(pages):
    if not isinstance(pages,list) or len(pages)!=5:raise ValueError("five_native_pages_required")
    expect={("english",1),("english",2),("arabic",1),("arabic",2),("arabic",3)}
    seen=set();violations=[]
    for p in pages:
        if not isinstance(p,dict) or not isinstance(p.get("boxes"),list):
            raise ValueError("missing_layout_geometry")
        pair=(p.get("product"),p.get("page"))
        if pair not in expect or pair in seen:raise ValueError("invalid_page_manifest")
        seen.add(pair)
        if p.get("width")!=3840 or p.get("height")!=2160:
            violations.append("wrong_4k_dimensions");continue
        if not isinstance(p.get("sha256"),str) or len(p["sha256"])!=64:
            raise ValueError("page_digest_missing")
        for box in p["boxes"]:
            if (not isinstance(box,dict) or
                any(type(box.get(k)) not in (float,int) for k in ("x","y","w","h","font_px"))):
                raise ValueError("invalid_text_geometry")
            x,y,w,h=tuple(box[k] for k in ("x","y","w","h"))
            if w<=0 or h<=0 or x<0 or y<0 or x+w>3840 or y+h>2160:
                violations.append("text_box_clipped")
            if box["font_px"]<28:
                violations.append("too_small_at_4k")
    return {"schema":"aggregateit-v2-b60-geometry/1","boxes_checked":sum(len(x["boxes"]) for x in pages),
            "violations":sorted(set(violations)),"synthetic_metadata_only":True,
            "original_publisher_visual_defects_cleared":False,
            "physical_phone_reviewed":False,"can_release":False}

def assess_original_visual_status(*,original_manifest, candidate_geometry=None):
    if not isinstance(original_manifest,dict) or original_manifest.get("schema")!="aggregateit-v2-b53-original-visual-inventory/1":
        raise ValueError("unknown_original_visual_baseline")
    if set(original_manifest.get("known_defects",[]))!=set(KNOWN_DEFECTS):
        raise ValueError("missing_original_visual_defects")
    # Bounding boxes are only a technical lint. They cannot fix title/lead
    # mismatches, actual readability, UAE coverage, or thematic repetition.
    lint=inspect_layout_geometry(candidate_geometry) if candidate_geometry is not None else None
    return {"schema":"aggregateit-v2-b60-visual-acceptance/1",
            "original_known_defects":list(KNOWN_DEFECTS),
            "candidate_geometry":lint,
            "source_synced_v2_original_page_review":False,
            "editorial_and_visual_defects_resolved":False,
            "physical_discord_client_visual_receipt_verified":False,
            "can_release":False}
