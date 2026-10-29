"""Offline same-fixture V1/V2 processing parity benchmark.

This reports *measured disagreement* rather than claiming production equivalence.
No network, posting, mutation or synthetic 'pass' against live V1.
"""
from __future__ import annotations
from v2_event_intelligence import arabic_filter,cluster_candidates,multilingual_candidates,event_evolution
from v2_v1_processing_bridge import arabic_relevance_gate,event_duplicate_decision
from v2_v1_full_scoring import score_english_v1

FIXTURES=(
 {"id":"ar-security","language":"ar","region":"iran","title":"هجوم صاروخي على الحدود","expected":True},
 {"id":"ar-diplomacy","language":"ar","region":"somalia","title":"مباحثات دبلوماسية في الصومال بشأن العلاقات الإقليمية","expected":True},
 {"id":"ar-routine","language":"ar","region":"gcc","title":"ازدحام مروري بسبب مباراة","expected":False},
 {"id":"ar-cultural","language":"ar","region":"somalia","title":"مهرجان ثقافي في الصومال","expected":False},
 {"id":"ar-unknown-region","language":"ar","region":None,"title":"هجوم صاروخي على الحدود","expected":False},
)
def benchmark():
 rows=[]
 for f in FIXTURES:
  v1=arabic_relevance_gate(f["title"])
  v2=arabic_filter(f["title"],region=f["region"])
  rows.append({"id":f["id"],"v1_bridge_admit":v1,"v2_admit":v2["admit"],
               "expected":f["expected"],"v2_expected_match":v2["admit"]==f["expected"],
               "bridge_disagreement":v1!=v2["admit"],"reason":v2["reason"]})
 english=score_english_v1("Fed announces inflation update","The Federal Reserve discusses CPI",source_name="Reuters")
 events=[{"event_id":"a","title":"Iran strikes Israel","region":"iran","source_id":"one"},
         {"event_id":"b","title":"Israel strikes Iran","region":"iran","source_id":"two"}]
 cluster=cluster_candidates(events)
 pair=multilingual_candidates([{"event_id":"a","region":"iran"}],[{"event_id":"c","region":"iran"}])
 history=event_evolution({"a":"v2","c":"v1"},{"a":"v1"})
 return {"schema":"aggregateit-v2-processing-parity-benchmark/1",
         "fixture_count":len(rows),"arabic":rows,
         "arabic_expected_matches":sum(x["v2_expected_match"] for x in rows),
         "arabic_bridge_disagreements":sum(x["bridge_disagreement"] for x in rows),
         "english_scoring":{"priority":english["priority"],"components":english["components"],
                            "actual_v1_output_compared":False},
         "event_clustering":{"review_pairs":len(cluster["review_pairs"]),"automatic_merges":cluster["automatic_merges"]},
         "multilingual":{"review_pairs":len(pair["pairs"]),"automatic_merges":pair["automatic_merges"]},
         "historical":{"statuses":history,"authenticated_fixture_only":True},
         "same_real_v1_v2_input_corpus":False,
         "production_parity_proven":False,"can_release":False}
if __name__=="__main__":
 import json
 print(json.dumps(benchmark(),ensure_ascii=False,indent=2))
