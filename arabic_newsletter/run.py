"""python -m arabic_newsletter.run [--sample | --audit | --preflight] [--send]."""
import argparse
import fcntl
import json
import os
import time
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
    modes.add_argument('--preflight',action='store_true'); modes.add_argument('--health-only',action='store_true')
    parser.add_argument('--probe-model',action='store_true'); parser.add_argument('--probe-discord',action='store_true')
    parser.add_argument('--long',action='store_true'); parser.add_argument('--send',action='store_true')
    parser.add_argument('--manual-now',action='store_true',help='Manual live assessment using the rolling six hours ending now; requires --send')
    parser.add_argument('--manual-file',type=Path,help='Render/send a reviewed evidence-bound briefing JSON without calling the external LLM')
    parser.add_argument('--end',help='ISO timestamp for a replay; requires timezone')
    parser.add_argument('--output',type=Path,default=ROOT/'runtime'/'output')
    args=parser.parse_args()
    if args.sample and args.send: parser.error('Synthetic samples cannot be delivered')
    if args.end and args.send: parser.error('Historical replay cannot be delivered')
    if args.preflight and args.send: parser.error('--preflight never publishes; use --probe-discord to test routing')
    if args.manual_now and not args.send: parser.error('--manual-now requires --send')
    if args.manual_now and (args.sample or args.audit or args.preflight or args.health_only or args.end or args.manual_file): parser.error('--manual-now is only for a current manual live edition')
    if args.manual_file and (args.sample or args.audit or args.preflight or args.health_only or args.end): parser.error('--manual-file cannot be combined with another mode')
    state_dir=Path(os.getenv('ARABIC_STATE_DIR',str(ROOT/'runtime'/'state')))
    state_dir.mkdir(parents=True,exist_ok=True)
    with (state_dir/'run.lock').open('w') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        state=State(state_dir)
        try:
            if args.preflight:
                client=Client(state)
                if args.probe_model:
                    translation=client.probe_text(
                        'Translate this sentence into Modern Standard Arabic only, with no explanation: '
                        'Regional security coordination remains under review.'
                    )
                    if not is_arabic(translation):
                        raise RuntimeError('Arabic LLM translation probe failed: Arabic output not detected')
                    print('Arabic model connectivity/translation live probe passed')
                if args.probe_discord: webhook_info()
                print('Arabic configuration preflight passed' if args.probe_model else 'Arabic configuration present; API authentication not tested'); return
            if args.audit: audit(args.output); return
            if args.health_only:
                end=datetime.now(timezone.utc).astimezone(UAE).replace(microsecond=0)
                start=end-timedelta(hours=6)
                audit_registry=ROOT/'runtime'/'audit'/'discovered_sources.json'
                registry=json.loads(audit_registry.read_text()) if audit_registry.exists() else None
                articles,health=collect(start,end,registry=registry)
                args.output.mkdir(parents=True,exist_ok=True)
                write_json(args.output/'collection_health.json',health)
                write_json(args.output/'source_evidence.json',articles)
                healthy_by_region={}
                for region in REGIONS:
                    healthy_by_region[region]=[
                        h for h in health
                        if h.get('region')==region
                        and h.get('status') in ('active','social_only')
                        and int(h.get('items') or 0)>0
                    ]
                summary={
                  'window_start':start.isoformat(),'window_end':end.isoformat(),
                  'healthy_regions':sorted(r for r,v in healthy_by_region.items() if v),
                  'unhealthy_regions':sorted(r for r,v in healthy_by_region.items() if not v),
                  'active_extractors_by_region':{r:len(v) for r,v in healthy_by_region.items()},
                  'substitutes_used':sum(bool(h.get('substitute')) for h in health),
                  'articles_in_window':len(articles),
                }
                write_json(args.output/'source_health_summary.json',summary)
                if summary['unhealthy_regions']:
                    raise RuntimeError('Regional source-health gate failed after same-region substitution: '+','.join(summary['unhealthy_regions']))
                print('Arabic source-health gate passed for all regions; articles in window:',len(articles))
                return
            if args.sample:
                brief=fixture(args.long)
                brief['morning']=False
                brief['analysis']=brief.get('analysis') or {}

            elif args.manual_file:
                brief=json.loads(args.manual_file.read_text(encoding='utf-8'))
                if brief.get('sample') or not brief.get('events'):
                    raise RuntimeError('Manual briefing must be real and contain events')
                if not brief.get('window_end') or not brief.get('window_start'):
                    raise RuntimeError('Manual briefing requires an explicit evidence window')
                source_health=brief.get('source_health') or {}
                unresolved=source_health.get('unresolved_regions',source_health.get('unhealthy_regions',[]))
                if unresolved:
                    raise RuntimeError('Manual briefing source-health gate failed: '+','.join(unresolved))
                llm_health=brief.get('llm_health') or {}
                if llm_health.get('status')!='ok' or not llm_health.get('all_event_text_arabic') or not llm_health.get('analysis_present'):
                    raise RuntimeError('Manual briefing LLM/translation health gate failed')
                translated=[' '.join(str(e.get(k,'')) for k in ('title_ar','summary_ar','assessment_ar','watch_ar')) for e in brief['events']]
                if not all(is_arabic(t) for t in translated):
                    raise RuntimeError('Manual briefing contains non-Arabic event prose')
                for e in brief['events']:
                    if not e.get('sources') or any(not s.get('url') for s in e.get('sources',[])):
                        raise RuntimeError('Manual briefing contains an event without source attribution')
                edition=brief['window_end']
                if args.send:
                    webhook_info()
                    prior=state.delivery(edition)
                    if prior and prior[0]=='sent': print('Manual edition already delivered'); return
                    if prior and prior[0] in ('sending','uncertain'):
                        raise RuntimeError('Previous manual delivery is ambiguous and requires reconciliation')

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
                phase=time.monotonic(); print('Arabic phase start: collect',flush=True)
                articles,health=collect(collection_start,end,registry=registry)
                print(f'Arabic phase complete: collect elapsed_s={time.monotonic()-phase:.1f}',flush=True)
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
                    phase=time.monotonic(); print('Arabic phase start: synthesize',flush=True)
                    events,rejected=synthesize(articles,state)
                    print(f'Arabic phase complete: synthesize elapsed_s={time.monotonic()-phase:.1f}',flush=True)
                finally:
                    write_json(args.output/'editorial_draft.json',state.get('last_editorial_draft') or {})
                    write_json(args.output/'editorial_review_raw.json',state.get('last_editorial_review_raw') or {})
                    write_json(args.output/'editorial_review.json',state.get('last_editorial_review') or [])
                phase=time.monotonic(); print('Arabic phase start: analysis',flush=True)
                analysis=build_analysis(events,state,morning=morning)
                print(f'Arabic phase complete: analysis elapsed_s={time.monotonic()-phase:.1f}',flush=True)
                translated=[
                  ' '.join(str(e.get(k,'')) for k in ('title_ar','summary_ar','assessment_ar','watch_ar'))
                  for e in events
                ]
                llm_health={
                  'model':state.get('last_model_used') or os.getenv('ARABIC_LLM_MODEL'),
                  'events_returned':len(events),
                  'all_event_text_arabic':all(is_arabic(t) for t in translated) if translated else True,
                  'analysis_present':bool((analysis or {}).get('situation_ar')),
                  'status':'ok',
                }
                if args.send and (not llm_health['all_event_text_arabic'] or (events and not llm_health['analysis_present'])):
                    raise RuntimeError('Arabic LLM extraction/translation validation failed')
                write_json(args.output/'llm_health.json',llm_health)
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
            encoded=json.dumps(brief,ensure_ascii=False)
            forbidden=('\ufffd','\u25a1','\u25a0','\ufeff','\u202a','\u202b','\u202c','\u202d','\u202e','\u2066','\u2067','\u2068','\u2069')
            if any(mark in encoded for mark in forbidden):
                raise RuntimeError('Encoding hygiene gate failed before rendering')
            phase=time.monotonic(); print('Arabic phase start: render',flush=True)
            paths,clipped=render(brief,args.output)
            print(f'Arabic phase complete: render elapsed_s={time.monotonic()-phase:.1f}',flush=True)
            write_json(args.output/'briefing.json',brief)
            write_json(args.output/'render_report.json',{'visually_shortened_blocks':clipped,'full_text':'sources-ar.txt','dimensions':[3840,2160],'pages':len(paths)})
            refs=args.output/'sources-ar.txt'; references(brief,refs)
            if args.send:
                phase=time.monotonic(); print('Arabic phase start: discord_send',flush=True)
                message_id=send(state,edition,paths)
                print(f'Arabic phase complete: discord_send elapsed_s={time.monotonic()-phase:.1f}',flush=True)
                if brief['events']:
                    keep=('region','topic','title_ar','summary_ar','assessment_ar','watch_ar','severity','fingerprint','source_ids')
                    state.put('previous_events',[{k:e.get(k) for k in keep} for e in brief['events']])
                print('Arabic edition delivered; message ID:',message_id)
            else: print('Arabic slides rendered; no delivery requested')
        finally: state.close()

if __name__=='__main__': main()
