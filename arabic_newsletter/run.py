"""python -m arabic_newsletter.run [--sample | --audit | --preflight] [--send]."""
import argparse
import fcntl
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from .core import ROOT, State, edition_window, live_window, write_json
from .collect import audit, collect
from .editor import Client, synthesize, build_analysis
from .delivery import webhook_url, send
from .render import render, references
from .sample import fixture

def main():
    parser=argparse.ArgumentParser()
    modes=parser.add_mutually_exclusive_group()
    modes.add_argument('--sample',action='store_true'); modes.add_argument('--audit',action='store_true')
    modes.add_argument('--preflight',action='store_true')
    parser.add_argument('--probe-model',action='store_true'); parser.add_argument('--long',action='store_true'); parser.add_argument('--send',action='store_true')
    parser.add_argument('--end',help='ISO timestamp for a replay; requires timezone')
    parser.add_argument('--output',type=Path,default=ROOT/'runtime'/'output')
    args=parser.parse_args()
    if args.sample and args.send: parser.error('Synthetic samples cannot be delivered')
    if args.end and args.send: parser.error('Historical replay cannot be delivered')
    state_dir=Path(os.getenv('ARABIC_STATE_DIR',str(ROOT/'runtime'/'state')))
    state_dir.mkdir(parents=True,exist_ok=True)
    with (state_dir/'run.lock').open('w') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        state=State(state_dir)
        try:
            if args.preflight:
                client=Client(state)
                if args.probe_model:
                    client.chat('Return JSON only.',{'request':'Return {"ok":true}'},30)
                    print('Arabic model API probe passed')
                if args.send: webhook_url()
                print('Arabic configuration preflight passed' if args.probe_model else 'Arabic configuration present; API authentication not tested'); return
            if args.audit: audit(args.output); return
            if args.sample:
                brief=fixture(args.long)
                brief['morning']=False
                brief['analysis']={}

            else:
                now=datetime.fromisoformat(args.end) if args.end else None
                if now and now.tzinfo is None: parser.error('--end must include a timezone')
                start,end=edition_window(now) if now else live_window(); edition=end.isoformat()
                morning=end.hour==6
                # The 06:00 UAE edition is the start-of-day product and carries
                # a wider overnight collection window for a heavier synthesis.
                collection_start=end-timedelta(hours=12) if end.hour==6 else start
                if args.send:
                    webhook_url(); Client(state)
                    prior=state.delivery(edition)
                    if prior and prior[0]=='sent': print('Edition already delivered'); return
                    if prior: raise RuntimeError('Previous delivery requires reconciliation')
                audit_registry=ROOT/'runtime'/'audit'/'discovered_sources.json'
                registry=json.loads(audit_registry.read_text()) if audit_registry.exists() else None
                articles,health=collect(collection_start,end,registry=registry)
                args.output.mkdir(parents=True,exist_ok=True)
                write_json(args.output/'collection_health.json',health)
                write_json(args.output/'source_evidence.json',articles)
                if not any(r['status'] in ('active','social_only') for r in health): raise RuntimeError('All source collection failed; publication blocked')
                try:
                    events,rejected=synthesize(articles,state)
                finally:
                    write_json(args.output/'editorial_draft.json',state.get('last_editorial_draft') or {})
                    write_json(args.output/'editorial_review.json',state.get('last_editorial_review') or [])
                analysis=build_analysis(events,state,morning=morning)
                brief=dict(sample=False,window_start=collection_start.isoformat(),window_end=end.isoformat(),events=events,
                  input_count=len(articles),health=health,rejected=rejected,analysis=analysis,morning=morning,
                  previous_events=state.get('previous_events') or [])
                if args.send and not events: raise RuntimeError('No qualified events; empty publication blocked, see health artifact')
            paths,clipped=render(brief,args.output)
            write_json(args.output/'briefing.json',brief)
            write_json(args.output/'render_report.json',{'visually_shortened_blocks':clipped,'full_text':'sources-ar.txt','dimensions':[3840,2160]})
            refs=args.output/'sources-ar.txt'; references(brief,refs)
            if args.send:
                message_id=send(state,brief['window_end'],paths)
                state.put('previous_events',[{'title_ar':e['title_ar'],'summary_ar':e['summary_ar'],'source_ids':e['source_ids']} for e in brief['events']])
                print('Arabic edition delivered; message ID:',message_id)
            else: print('Arabic slides rendered; no delivery requested')
        finally: state.close()

if __name__=='__main__': main()
