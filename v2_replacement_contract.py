"""Option A V1 delivery/cadence contract for V2 preparation.

Inspects repository text without loading credentials or invoking anything.
The current V2 shadow job must NEVER publish or run on a production schedule.
This is continuity inspection, not permission to switch production.
"""
from __future__ import annotations
import json
from pathlib import Path

REQUIRED={
 ".github/workflows/engine.yml":{
  "hourly_engine_schedule":'cron: "7 * * * *"',
  "engine_delivery_disabled":'ENGINE_DELIVERY: "false"',
  "engine_original_entrypoint":"run: python main.py",
 },
 ".github/workflows/slide.yml":{
  "gazette_schedule":'cron: "30 11 * * *"',
  "gazette_original_entrypoint":"run: python slide.py",
  "gazette_route":"DISCORD_WEBHOOK: ${{ secrets.DISCORD_WEBHOOK }}",
  "gazette_channel_validation":"DISCORD_EXPECTED_CHANNEL_ID:",
 },
 ".github/workflows/arabic-scheduler.yml":{
  "arabic_0600_schedule":'cron: "0 2 * * *"',
  "arabic_1200_schedule":'cron: "0 8 * * *"',
  "arabic_1800_schedule":'cron: "0 14 * * *"',
  "arabic_0000_schedule":'cron: "0 20 * * *"',
  "arabic_original_entrypoint":"run: python arabic_live_v2.py",
  "arabic_route":"DISCORD_WEBHOOK_ARABIC: ${{ secrets.DISCORD_WEBHOOK_ARABIC }}",
  "arabic_channel_validation":"DISCORD_ARABIC_EXPECTED_CHANNEL_ID:",
 },
 ".github/workflows/tv_refresh.yml":{
  "market_weekly":'cron: "30 12 * * 1"',
  "market_session":'cron: "59 13-19 * * 1-5"',
  "market_close":'cron: "30 20 * * 1-5"',
 },
 ".github/workflows/backup.yml":{
  "weekly_backup":'cron: "0 6 * * 0"',
 },
 "arabic_newsletter/PRODUCT_RULES.md":{
  "arabic_three_slides":"Three slides remain the production format",
  "arabic_4k":"3840x2160 PNG",
  "arabic_font":"Approved production font: Noto Sans Arabic",
 },
 ".github/workflows/v2-b80-b83-live-acceptance.yml":{
  "shadow_gazette_no_post":"DISCORD_WEBHOOK: ''",
  "shadow_arabic_no_post":"DISCORD_WEBHOOK_ARABIC: ''",
  "shadow_actions_read_only":"contents: read",
 },
}

def check_contract(root:Path)->dict:
 root=Path(root)
 violations=[]
 for relative,assertions in REQUIRED.items():
  path=root/relative
  if not path.is_file():
   violations.append(relative+":missing_file")
   continue
  raw=path.read_text(encoding="utf8")
  for label,token in assertions.items():
   if token not in raw:violations.append(relative+":"+label)
 # Only V2 shadow can run on push/manual. No production schedule before cutover.
 shadow=root/".github/workflows/v2-b80-b83-live-acceptance.yml"
 if shadow.is_file():
  raw=shadow.read_text(encoding="utf8")
  if "\n  schedule:" in raw:violations.append("shadow_has_production_schedule")
  if raw.count("DISCORD_WEBHOOK: ''")!=1 or raw.count("DISCORD_WEBHOOK_ARABIC: ''")!=1:
   violations.append("shadow_discord_not_explicitly_disabled")
 return {"schema":"aggregateit-v2-replacement-continuity/1",
         "continuity_verified":not violations,
         "checked_files":len(REQUIRED),
         "violations":violations,
         "production_schedules_modified":False if not violations else "unverified",
         "production_delivery_invoked":False,
         "cutover_authorized":False}

if __name__=="__main__":
 print(json.dumps(check_contract(Path(__file__).resolve().parent),ensure_ascii=False))
