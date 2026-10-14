import {test} from 'node:test';
import assert from 'node:assert/strict';
import {Cadence,schedules,slotStart} from './scheduler.mjs';
test('external schedule matches repository UTC schedules',()=>{
 const now=Date.parse('2026-10-14T13:30:00Z')/1000;
 assert.equal(new Date(slotStart(schedules[1],now)*1000).toISOString(),'2026-10-14T08:00:00.000Z');
 assert.equal(new Date(slotStart(schedules[2],now)*1000).toISOString(),'2026-10-14T11:30:00.000Z');
});
test('no credential cannot dispatch',async()=>{
 const r=await new Cadence({},{}).fetch();assert.equal(r.status,503);
});
test('accepted dispatches are durable, native pending runs are not repeated',async()=>{
 const data=new Map(); const state={blockConcurrencyWhile:f=>f(),storage:{get:async k=>data.get(k),put:async(k,v)=>data.set(k,v),list:async()=>data,delete:async k=>data.delete(k)}};
 const original=globalThis.fetch;let posts=0;
 globalThis.fetch=async(url,opts)=>{
  if(opts.method==='POST'){posts++;const body=JSON.parse(opts.body);assert.equal(body.ref,'main');assert.ok(body.inputs.scheduler_slot);return new Response(null,{status:204});}
  return Response.json({workflow_runs:[]});
 };
 try {
  const c=new Cadence(state,{GITHUB_DISPATCH_TOKEN:'synthetic'});await c.fetch();const first=posts;await c.fetch();assert.equal(posts,first);assert.ok(first>0);
  data.clear();globalThis.fetch=async()=>Response.json({workflow_runs:[{created_at:new Date().toISOString(),status:'queued'}]});
  await c.fetch();assert.equal(data.size,0);
 } finally {globalThis.fetch=original;}
});
