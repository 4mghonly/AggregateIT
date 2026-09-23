"""python -m arabic_newsletter.run [--sample | --audit | --preflight] [--send]."""
import argparse
import fcntl
import json
import os
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from .core import ROOT, REGIONS, State, UAE, edition_window, live_window, write_json
from .collect import audit, collect, health_summary
from .editor import Client, synthesize, build_analysis, is_arabic
from .delivery import webhook_info, send
from .render import render, references
from .sample import fixture

def main():
    parser=argparse.ArgumentParser()
    modes=parser.add_mutually_exclusive_group()
    modes.add_argument('--sample',action='store_true'); modes.add_argument('--audit',action='store_true')
    modes.add_argument('--preflight',action='store_true')
    parser.add_argument('--probe-model',action='store_true'); parser.add_argument('--probe-discord',action='store_true')
    parser.add_argument('--long',action='store_true'); parser.add_argument('--send',action='store_true')
    parser.add_argument('--manual-now',action='store_true',help='Manual live assessment using the rolling six hours ending now; requires --send')
    parser.add_argument('--end',help='ISO timestamp for a replay; requires timezone')
    parser.add_argument('--output',type=Path,default=ROOT/'runtime'/'output')
    args=parser.parse_args()
    if args.sample and args.send: parser.error('Synthetic samples cannot be delivered')
    if args.end and args.send: parser.error('Historical replay cannot be delivered')
    if args.preflight and args.send: parser.error('--preflight never publishes; use --probe-discord to test routing')
    if args.manual_now and not args.send: parser.error('--manual-now requires --send')
    if args.manual_now and (args.sample or args.audit or args.preflight or args.end): parser.error('--manual-now is only for a current manual live edition')
    state_dir=Path(os.getenv('ARABIC_STATE_DIR',str(ROOT/'runtime'/'state')))
    state_dir.mkdir(parents=True,exist_ok=True)
    with (state_dir/'run.lock').open('w') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        state=State(state_dir)
        try:
            if args.preflight:
                client=Client(state)
                if args.probe_model:
                    probe=client.chat(
                        'Return JSON only. Translate the supplied English sentence into Modern Standard Arabic.',
                        {'text':'Regional security coordination remains under review.',
                         'schema':{'translation':'Arabic text only'}},
                        80,use_cache=False)
                    translation=str(probe.get('translation','')) if isinstance(probe,dict) else ''
                    if not is_arabic(translation):
                        raise RuntimeError('Arabic LLM translation probe failed: Arabic output not detected')
                    print('Arabic model extraction/translation live probe passed')
                if args.probe_discord: webhook_info()
                print('Arabic configuration preflight passed' if args.probe_model else 'Arabic configuration present; API authentication not tested'); return
            if args.audit: audit(args.output); return
            if args.sample:
                brief=fixture(args.long)
                brief['morning']=False
                brief['analysis']=brief.get('analysis') or {}

            else:
                if args.manual_now:
                    end=datetime.now(timezone.utc).astimezone(UAE).replace(microsecond=0)
                    start=end-timedelta(hours=6)
                    edition=end.isoformat()
                    morning=False
                    collection_start=start
                else:
                    now=datetime.fromisoformat(args.end) if args.end else None
                    if now and now.tzinfo is None: parser.error('--end must include a timezone')
                    start,end=edition_window(now) if now else live_window(); edition=end.isoformat()
                    morning=end.hour==6
                    # The 06:00 UAE edition is the start-of-day product and carries
                    # a wider overnight collection window for a heavier synthesis.
                    collection_start=end-timedelta(hours=12) if end.hour==6 else start
                if args.send:
                    webhook_info(); Client(state)
                    prior=state.delivery(edition)
                    if prior and prior[0]=='sent': print('Edition already delivered'); return
                    if prior and prior[0] in ('sending','uncertain'):
                        raise RuntimeError('Previous delivery is ambiguous and requires reconciliation')
                    # Confirmed failed HTTP deliveries are safe to retry; send() clears them.
                audit_registry=ROOT/'runtime'/'audit'/'discovered_sources.json'
                registry=json.loads(audit_registry.read_text()) if audit_registry.exists() else None
                articles,health=collect(collection_start,end,registry=registry)
                args.output.mkdir(parents=True,exist_ok=True)
                write_json(args.output/'collection_health.json',health)
                write_json(args.output/'source_evidence.json',articles)
                source_health=health_summary(health)
                write_json(args.output/'source_health_summary.json',source_health)
                if not any(r['status'] in ('active','social_only') for r in health):
                    raise RuntimeError('All source collection failed; publication blocked')
                if source_health['unresolved_regions']:
                    raise RuntimeError('Regional source-health gate failed after same-region substitution: '+','.join(source_health['unresolved_regions']))
                if args.send and not articles:
                    raise RuntimeError('Live extraction yielded no dated relevant articles; publication blocked')
                try:
                    events,rejected=synthesize(articles,state)
                finally:
                    write_json(args.output/'editorial_draft.json',state.get('last_editorial_draft') or {})
                    write_json(args.output/'editorial_review_raw.json',state.get('last_editorial_review_raw') or {})
                    write_json(args.output/'editorial_review.json',state.get('last_editorial_review') or [])
                analysis=build_analysis(events,state,morning=morning)
                event_sources={s.get('id'):s for e in events for s in e.get('sources',[]) if s.get('id')}
                coverage={
                  'article_languages':dict(Counter(a.get('language','unknown') for a in articles)),
                  'active_source_languages':dict(Counter(h.get('language','unknown') for h in health if h.get('status') in ('active','social_only'))),
                  'event_source_languages':dict(Counter(s.get('language','unknown') for s in event_sources.values())),
                  'event_source_count':len(event_sources),
                  'non_arabic_event_sources':sum(s.get('language')!='ar' for s in event_sources.values()),
                  'healthy_regions':sorted(r for r,v in source_health['regions'].items() if v['healthy_extractors']),
                  'active_extractors_by_region':{r:v['healthy_extractors'] for r,v in source_health['regions'].items()},
                  'substitutes_used':sum(v['substitutes_used'] for v in source_health['regions'].values()),
                }
                brief=dict(sample=False,window_start=collection_start.isoformat(),window_end=end.isoformat(),events=events,
                  input_count=len(articles),health=health,rejected=rejected,analysis=analysis,morning=morning,
                  coverage=coverage,source_health=source_health,empty_cycle=not bool(events),previous_events=state.get('previous_events') or [])
                if args.send and not events:
                    print('No qualified events; delivering an explicit no-material-change status briefing',flush=True)
            paths,clipped=render(brief,args.output)
            write_json(args.output/'briefing.json',brief)
            write_json(args.output/'render_report.json',{'visually_shortened_blocks':clipped,'full_text':'sources-ar.txt','dimensions':[3840,2160]})
            refs=args.output/'sources-ar.txt'; references(brief,refs)
            if args.send:
                message_id=send(state,edition,paths)
                if brief['events']:
                    keep=('region','topic','title_ar','summary_ar','assessment_ar','watch_ar','severity','fingerprint','source_ids')
                    state.put('previous_events',[{k:e.get(k) for k in keep} for e in brief['events']])
                print('Arabic edition delivered; message ID:',message_id)
            else: print('Arabic slides rendered; no delivery requested')
        finally: state.close()

if __name__=='__main__': main()
