"""Evidence-derived coverage diagnostics; never manufacture reporting."""
from collections import Counter

def assess_coverage(products):
    if not isinstance(products,dict):
        raise ValueError("invalid_products")
    result={}
    for product,items in products.items():
        if not isinstance(items,list):
            raise ValueError("invalid_coverage_items")
        publishers=Counter(row["source_id"] for row in items if row.get("source_id"))
        regions={row["region"] for row in items if row.get("region")}
        n=sum(publishers.values())
        result[product]={
            "story_count":len(items),
            "publisher_count":len(publishers),
            "region_count":len(regions),
            "represented_regions":sorted(regions),
            "concentration":round(max(publishers.values())/n,3) if n else None,
            "diverse_sources":len(publishers)>=3,
            "sufficient_geographic_breadth":len(regions)>=5,
            "quality_gate":"REVIEW" if len(publishers)<3 or len(regions)<5 else "COVERAGE_METRICS_PASS",
        }
    return result
