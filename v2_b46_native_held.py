"""B46 stage 5: real source-backed, held native five-page quality smoke test.

Calls existing English and Arabic *real* native renderers on the B3/B4-held
source excerpts. Output bytes are written only to caller-owned disposable dir.
No rights approval, publisher fact verification, LLM or Discord forwarding.
"""
from __future__ import annotations
from hashlib import sha256
from pathlib import Path
from PIL import Image
from v2_native_evidence_render import render_held_editions

def render_genuine_held(editorial:dict, *, output_dir:Path)->dict:
    if (not isinstance(editorial,dict) or
        editorial.get("schema")!="aggregateit-v2-b46-article-editorial/1" or
        editorial.get("can_send") is not False or
        editorial.get("source_story_factual_accuracy_verified") is not False):
        raise ValueError("untrusted_editorial_bridge")
    products=editorial.get("products")
    if not isinstance(products,dict) or set(products)!={"english","arabic"}:
        raise ValueError("both_products_required")
    plans={}
    for p,lang in (("english","en"),("arabic","ar")):
        product=products[p]
        if (product.get("no_publication_authority") is not True
            or product.get("story_count",0)<1
            or product.get("newsroom",{}).get("delivery_authorized") is not False):
            raise ValueError("bilingual_evidence_required")
        plan=product.get("editorial_plan")
        if (not isinstance(plan,dict) or plan.get("product")!=p
            or plan.get("language")!=lang or plan.get("delivery_authorized") is not False
            or not isinstance(plan.get("items"),list) or len(plan["items"])!=product["story_count"]):
            raise ValueError("untrusted_held_plan")
        for item in plan["items"]:
            ev=item.get("evidence")
            if not isinstance(ev,dict) or not ev.get("excerpt_id") or ev.get("original_language")!=lang:
                raise ValueError("unverified_original_excerpt")
        plans[p]=plan
    if plans["english"]["slot_id"]!=plans["arabic"]["slot_id"]:
        raise ValueError("mismatched_edition_slot")
    out=Path(output_dir)
    if out.is_symlink() or (out.exists() and any(out.iterdir())):
        raise ValueError("native_output_requires_empty_directory")
    rendered=render_held_editions(plans["english"],plans["arabic"],
                                   slot_id=plans["english"]["slot_id"],output_dir=out)
    if (rendered.get("schema")!="aggregateit-v2-native-no-post-pages/1"
        or rendered.get("delivery_authorized") is not False):
        raise ValueError("native_renderer_claims_delivery")
    pages=rendered.get("pages")
    if not isinstance(pages,list) or len(pages)!=5:
        raise ValueError("held_native_page_count")
    expected={("english",1),("english",2),("arabic",1),("arabic",2),("arabic",3)}
    if {(p["product"],p["page"]) for p in pages}!=expected:
        raise ValueError("unexpected_product_page_numbers")
    receipt=[]
    for p in pages:
        file=out/p["path"]
        if file.is_symlink() or file.parent!=out:
            raise ValueError("unsafe_renderer_path")
        body=file.read_bytes()
        if sha256(body).hexdigest()!=p["sha256"]:
            raise ValueError("native_image_digest_mismatch")
        with Image.open(file) as image:
            if image.format!="PNG" or image.size!=(3840,2160):
                raise ValueError("bad_4k_native_image")
            image.verify()
        receipt.append({"product":p["product"],"page":p["page"],
                        "sha256":p["sha256"],"dimensions":[3840,2160]})
    return {"schema":"aggregateit-v2-b46-native-held/1",
            "real_publisher_source_excerpt_count":editorial["admitted_articles"],
            "native_pages":receipt,"source_original_language_required":True,
            "publisher_facts_verified":False,"publishing_rights_verified":False,
            "translation_model_called":False,
            "status":"HELD_VALID_NATIVE_PAGES","discord_sent":False,"can_release":False}
