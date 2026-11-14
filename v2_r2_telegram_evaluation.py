"""Held R2 bilingual provider evaluation and explicitly requested Telegram report.

Only sends a clearly marked test report, never editorial pages or articles.
"""
import json,os,urllib.request,urllib.error
from v2_r2_http_transport import make_http_caller
from v2_r2_model_adapter import make_analysis_provider

FIXTURES={
 "english":{"event_id":"test-en","evidence":{"excerpt_id":"test-en-ex","quote":"Officials proposed two clinics, but funding was not approved.","source_url":"https://example.org/english-test"}},
 "arabic":{"event_id":"test-ar","evidence":{"excerpt_id":"test-ar-ex","quote":"اقترح المسؤولون إنشاء عيادتين لكن التمويل لم تتم الموافقة عليه.","source_url":"https://example.org/arabic-test"}}
}
def evaluate():
 results={}
 for role,prefix in (("primary","V2_LLM_"),("fallback","V2_LLM_FALLBACK_")):
  base=os.getenv(prefix+"BASE_URL","");model=os.getenv(prefix+"MODEL","");key=os.getenv(prefix+"API_KEY","")
  if not all((base,model,key)):
   results[role]={"status":"HOLD_MISSING_CONFIG","languages":{}}
   continue
  languages={}
  for lang,item in FIXTURES.items():
   try:
    caller=make_http_caller(base_url=base,model=model,api_key=key)
    candidates=make_analysis_provider(caller=caller)(product=lang,items=[item],as_of="2026-11-14T12:00:00+00:00")
    if not candidates:
     languages[lang]="ABSTAINED"
    else:
     assessment=candidates[0]["assessment"]
     languages[lang]="STRUCTURAL_PASS_UNVERIFIED"
     # No claim that language, accuracy, negation or entailment is proven.
   except Exception as exc:
    languages[lang]="HOLD_"+type(exc).__name__
  results[role]={"status":"EVALUATED","languages":languages}
 return {"schema":"aggregateit-v2-r2-bilingual-model-evaluation/1",
         "results":results,"synthetic_evidence_only":True,
         "independent_semantic_review":False,"real_publisher_evidence_evaluated":False,
         "editorial_release_authorized":False}

def send_report(report):
 token=os.getenv("V2_TELEGRAM_BOT_TOKEN","")
 if not token or any(x in token for x in "\r\n /"):return {"status":"HOLD_TELEGRAM_TOKEN"}
 lines=["AggregateIT V2 — R2 MODEL ACCEPTANCE TEST (NOT A NEWS EDITION)",
        "Both model routes tested on self-authored English and Arabic evidence.",
        "Publisher evidence: NOT TESTED. Independent semantic accuracy: NOT VERIFIED."]
 for role,detail in report["results"].items():
  lines.append(role.upper()+": "+", ".join(k+"="+v for k,v in detail["languages"].items())+
               (" ("+detail["status"]+")"))
 lines.append("Editorial publication: NOT AUTHORIZED. No news edition was sent.")
 body="\n".join(lines)
 receipts={}
 for lang in ("ENGLISH","ARABIC"):
  chat=os.getenv("V2_TELEGRAM_CHAT_ID_"+lang,"")
  if not chat.startswith("-100") or not chat[1:].isdigit():
   receipts[lang]="HOLD_INVALID_DESTINATION";continue
  payload=json.dumps({"chat_id":chat,"text":body,"disable_notification":True}).encode()
  req=urllib.request.Request("https://api.telegram.org/bot"+token+"/sendMessage",
                            data=payload,headers={"Content-Type":"application/json"},method="POST")
  try:
   with urllib.request.urlopen(req,timeout=25) as resp: data=json.load(resp)
   receipts[lang]="SENT" if data.get("ok") and data.get("result",{}).get("message_id") else "HOLD_REJECTED"
  except Exception as exc:
   receipts[lang]="HOLD_"+type(exc).__name__
 return receipts
if __name__=="__main__":
 report=evaluate()
 report["telegram_delivery"]=send_report(report)
 print(json.dumps(report,sort_keys=True,ensure_ascii=False))
