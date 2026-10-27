"""B59-B62 zero-cost offline closure; evidence-limited and pre-canary HOLD."""
from __future__ import annotations
import argparse,json
from pathlib import Path
from v2_b59_semantic_guard import fixture_digest,inspect_known_translation
from v2_b60_original_edition_qa import KNOWN_DEFECTS,assess_original_visual_status
from v2_b61_week_lineage import evaluate_week_lineage
from v2_b62_precanary import evaluate_precanary

def run(*,config_path):
    cfg=json.loads(Path(config_path).read_text(encoding="utf8"))
    translation=inspect_known_translation("en-plan",
      "اقترح مسؤولون في الصومال 12 عيادة في 27 أكتوبر",
      "لم تتم الموافقة على الخطة ولم يتم تأكيد افتتاح أي عيادة.",
      original_sha256=fixture_digest("en-plan"))
    original={"schema":"aggregateit-v2-b53-original-visual-inventory/1",
               "known_defects":list(KNOWN_DEFECTS)}
    visual=assess_original_visual_status(original_manifest=original)
    weekly=evaluate_week_lineage([],as_of="2026-10-27T23:08:00+04:00")
    decision=evaluate_precanary(cfg,b59=translation,b60=visual,b61=weekly)
    return {"schema":"aggregateit-v2-b59-b62-execution/1",
      "b59":translation,"b60":visual,"b61":weekly,"b62":decision,
      "new_provider_requests":0,"discord_sent":False,"can_release":False}

if __name__=="__main__":
    args=argparse.ArgumentParser();args.add_argument("--config",type=Path,
     default=Path("config/v2/b58_staged_paid_models.json"))
    args.add_argument("--output",required=True,type=Path)
    parsed=args.parse_args()
    result=run(config_path=parsed.config)
    parsed.output.parent.mkdir(parents=True,exist_ok=True)
    parsed.output.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
    print(json.dumps({"b59_fixture_pass":result["b59"]["checks_passed"],
      "b60_original_defect_count":len(result["b60"]["original_known_defects"]),
      "b61_real_week_days":result["b61"]["observed_days"],
      "b62_open_release_blocks":len(result["b62"]["open_release_blocks"]),
      "paid_calls":0,"production_canary":False,"can_release":False}))
