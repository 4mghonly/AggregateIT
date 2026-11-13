"""Import real archived V2 editorial plans without inventing missing days."""
import argparse,json
from pathlib import Path
from v2_product_recovery import ProductHistory,build_weekly_intelligence
from v2_recovery_publication import ingest_editorial_plan,render_recovery_html

def backfill(archive_paths,db_path,output_dir):
    plans=[]
    for path in archive_paths:
        data=json.loads(Path(path).read_text(encoding="utf-8"))
        if data.get("schema")=="aggregateit-editorial-plan/1":
            plans.append(data)
        elif isinstance(data.get("products"),dict):
            for product in ("english","arabic"):
                row=data["products"].get(product,{})
                plan=row.get("editorial_plan")
                if plan is not None:plans.append(plan)
        else:raise ValueError("unsupported_archive_schema")
    if not plans:raise ValueError("no_editorial_plans")
    plans.sort(key=lambda p:p["as_of"])
    h=ProductHistory(db_path)
    counts={"english":0,"arabic":0}
    try:
        for plan in plans:
            counts[plan["product"]]+=ingest_editorial_plan(h,plan)
        out=Path(output_dir)
        out.mkdir(parents=True,exist_ok=True)
        reports={}
        end=max(p["as_of"][:10] for p in plans)
        for product,lang in (("english","en"),("arabic","ar")):
            report=build_weekly_intelligence(h,lang,end)
            (out/(product+"-weekly.html")).write_text(render_recovery_html(report),encoding="utf-8")
            reports[product]={"stored":counts[product],"days_observed":report["days_observed"],
                              "complete_week":report["complete_week"],"events":report["total_events"]}
        return reports
    finally:h.close()

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("archives",nargs="+",type=Path)
    p.add_argument("--database",type=Path,required=True)
    p.add_argument("--output-dir",type=Path,required=True)
    a=p.parse_args()
    print(json.dumps(backfill(a.archives,a.database,a.output_dir),ensure_ascii=False,indent=2))
