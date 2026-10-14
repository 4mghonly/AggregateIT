// Independent Cloudflare cadence. No Discord/LLM credentials are used here.
export const schedules = [
  {file:'engine.yml',period:3600,offset:420,inputs:{dry_run:false}},
  {file:'arabic-scheduler.yml',period:21600,offset:7200,inputs:{}},
  {file:'slide.yml',period:86400,offset:41400,inputs:{}}
];
export const slotStart = (s,now) => Math.floor((now-s.offset)/s.period)*s.period+s.offset;
export class Cadence {
  constructor(state,env) { this.state=state;this.env=env; }
  async fetch() {
    if (!this.env.GITHUB_DISPATCH_TOKEN) return Response.json({ok:false,error:'missing_dispatch_credential'}, {status:503});
    // One durable coordinator serializes retries and remembers accepted slots.
    return this.state.blockConcurrencyWhile(async () => {
      const now=Math.floor(Date.now()/1000),results=[];
      for (const s of schedules) {
        const slot=slotStart(s,now),key=`${s.file}:${slot}`;
        if (now-slot<60 || await this.state.storage.get(key)) continue;
        const headers={'Authorization':`Bearer ${this.env.GITHUB_DISPATCH_TOKEN}`,'Accept':'application/vnd.github+json','User-Agent':'AggregateIT-cadence'};
        const base='https://api.github.com/repos/4mghonly/AggregateIT/actions/workflows/'+s.file;
        const check=await fetch(base+'/runs?branch=main&per_page=20',{headers});
        if (!check.ok) {results.push({workflow:s.file,error:'read_http_'+check.status});continue;}
        const runs=(await check.json()).workflow_runs;
        // Avoid racing a queued or running native edition for this slot.
        if(runs.some(r=>Date.parse(r.created_at)/1000>=slot && (r.status!=='completed'||r.conclusion==='success'))) {
          results.push({workflow:s.file,status:'native_run_present'});continue;
        }
        const sent=await fetch(base+'/dispatches',{method:'POST',headers:{...headers,'Content-Type':'application/json'},body:JSON.stringify({ref:'main',inputs:{...s.inputs,scheduler_slot:String(slot)}})});
        results.push({workflow:s.file,status:sent.status});
        if(sent.status===204) await this.state.storage.put(key,true);
      }
      // Keep only two days of dispatch receipts.
      const receipts=await this.state.storage.list();
      for(const key of receipts.keys()) if(Number(key.split(':').at(-1))<now-172800) await this.state.storage.delete(key);
      return Response.json({ok:!results.some(r=>r.error||typeof r.status==='number'&&r.status!==204),results});
    });
  }
}
export default {
  async scheduled(event,env,ctx) {
    ctx.waitUntil(env.CADENCE.get(env.CADENCE.idFromName('production')).fetch('https://cadence.internal/check').then(async r=>{console.log(await r.text());}));
  },
  async fetch() {return new Response('Scheduled service only',{status:404});}
};
