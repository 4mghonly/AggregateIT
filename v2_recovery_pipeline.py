"""Explicit opt-in bridge for B46 editorial output to persistent bilingual recovery."""
from pathlib import Path
from v2_product_recovery import ProductHistory,build_weekly_intelligence
from v2_recovery_publication import ingest_editorial_plan,render_recovery_html

def persist_bilingual_editorial(editorial,history_path,output_dir):
    products=editorial.get("products") if isinstance(editorial,dict) else None
    if not isinstance(products,dict) or not {"english","arabic"}<=set(products):
        raise ValueError("two_editorial_products_required")
    plans={}
    for product in ("english","arabic"):
        plan=products[product].get("editorial_plan")
        if not isinstance(plan,dict) or plan.get("product")!=product:
            raise ValueError("invalid_bilingual_plan")
        plans[product]=plan
    target=Path(output_dir)
    if target.is_symlink():raise ValueError("unsafe_output_path")
    target.mkdir(parents=True,exist_ok=True)
    h=ProductHistory(history_path)
    try:
        result={}
        for product,plan in plans.items():
            stored=ingest_editorial_plan(h,plan)
            lang="en" if product=="english" else "ar"
            report=build_weekly_intelligence(h,lang,plan["as_of"][:10])
            output=target/(product+"-weekly.html")
            output.write_text(render_recovery_html(report),encoding="utf-8")
            result[product]={"stored":stored,"days_observed":report["days_observed"],
                             "complete_week":report["complete_week"],"output":str(output)}
        return result
    finally:h.close()
