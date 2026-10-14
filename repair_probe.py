"""Production-shaped, independent route checks. No Discord credentials or posts."""
import os
# Workflow deliberately has only the Arabic-prefixed route secrets.
for key,value in list(os.environ.items()):
    if key.startswith('ARABIC_LLM_'): os.environ[key[len('ARABIC_'):]]=value
os.environ['LLM_MAX_CALLS']='20'
import json
import time
from pathlib import Path
from datetime import datetime,timezone
import llm
import arabic_live_v2 as ar
import slide
import main
from llm_response import rejection_reason

FACT='The ministry published a statement about border security. Officials said the statement contains no new operational details.'
AR_FACT='أصدرت الوزارة بياناً بشأن أمن الحدود. وقال مسؤولون إن البيان لا يتضمن تفاصيل عملياتية جديدة.'

def main_probe():
    results=[]
    ready={False:llm._route_complete(False),True:llm._route_complete(True)}
    for fallback in (False,True):
        name='fallback' if fallback else 'primary'
        llm._route_complete=lambda f=False,chosen=fallback: f==chosen and ready[f]
        llm._calls=0;llm._force_fallback=fallback
        llm.LEDGER_FILE='/tmp/repair-probe-'+name+'.json'
        Path(llm.LEDGER_FILE).unlink(missing_ok=True)
        route=ar._route('ARABIC_LLM_FALLBACK_' if fallback else 'ARABIC_LLM_')
        def gazette():
            fields={k:'One concise evidence-based sentence.' for k in slide.REQUIRED_KEYS}
            def valid(obj):
                if not all(isinstance(obj.get(k),str) and 10<=len(obj[k])<=600 for k in fields):raise ValueError('gazette_analysis_fields')
            prompt=slide.ANALYSIS_PROMPT.replace('__DATA__','\n'.join('Event '+str(i)+': '+FACT for i in range(10))).replace('__PREV__','No previous edition.')
            llm.chat_json([{'role':'system','content':'Output concise valid JSON only, one sentence per field, no reasoning.'},{'role':'user','content':prompt}],validator=valid,max_tokens=4096)
        def event():
            def valid(obj):
                ok,_,errs=main.validate_analysis(obj,evidence_text=FACT)
                if not ok:raise ValueError('analysis_schema: '+'; '.join(errs))
            prompt=main.EVENT_USER_PROMPT.format(cats='Security',prior_state='NEW EVENT',macro_context='No market evidence.',n_sources=1,sources_block=FACT)
            llm.chat_json([{'role':'system','content':main.EVENT_SYSTEM_PROMPT},{'role':'user','content':prompt}],validator=valid,max_tokens=4096)
        def translation():
            if not route:raise RuntimeError('missing_configuration')
            row={'title':'Ministry publishes border security statement','summary':FACT,'language':'en','source':'Synthetic probe'}
            raw=ar._route_call(route,ar.TRANSLATE_SYSTEM,{'items':[dict(row,index=0)]},max_tokens=4096,deadline=time.monotonic()+90)
            if len(ar._normalize_translations(raw,[row]))!=1:raise RuntimeError('translation_validation_failed')
        def analysis():
            if not route:raise RuntimeError('missing_configuration')
            payload={'events':[{'region':'iraq','title_ar':'بيان بشأن أمن الحدود','summary_ar':AR_FACT,'sources':['Synthetic probe']} for _ in range(17)]}
            ar._normalize_analysis(ar._route_call(route,ar.ANALYSIS_COMPACT_SYSTEM,payload,max_tokens=4096,deadline=time.monotonic()+90))
        for component,check in [('english_gazette',gazette),('english_event',event),('arabic_translation',translation),('arabic_analysis',analysis)]:
            start=time.monotonic()
            try:
                check();result={'route':name,'component':component,'ok':True}
            except Exception as exc:
                result={'route':name,'component':component,'ok':False,'error':rejection_reason(exc)}
            result['seconds']=round(time.monotonic()-start,1);results.append(result);print(json.dumps(result),flush=True)
    payload={'checked_at':datetime.now(timezone.utc).isoformat(),'routes':results,'all_ok':all(r['ok'] for r in results)}
    Path('reports').mkdir(exist_ok=True);Path('reports/repair_route_health.json').write_text(json.dumps(payload,indent=2))
    return 0 if payload['all_ok'] else 1

if __name__=='__main__':raise SystemExit(main_probe())
