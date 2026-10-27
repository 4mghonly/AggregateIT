/** B37 genuine source-headline mobile QA; no publication or external page requests. */
import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { createRequire } from 'node:module';
const require=createRequire(import.meta.url);
const {chromium}=require('playwright');
const record=JSON.parse(execFileSync('python3',['-B','v2_b37_private_capture.py'],
                   {cwd:process.cwd(),encoding:'utf8',timeout:65000}));
const output={schema:'aggregateit-v2-b37-live-mobile-qa/1',
              emulated_browser:'Chromium',real_phone_verified:false,
              discord_sent:false,news_verified:false,
              results:[],source_status:{},passed:false};
const browser=await chromium.launch({headless:true,args:['--no-sandbox']});
try{
  for(const product of ['english','arabic']){
    const item=record.results[product];
    output.source_status[product]={status:item.status,headlines_shown:item.headlines_shown??0,
      feed_sha256:item.capture_sha256??null,source_failure_class:item.failure_class??null};
    if(item.status!=='captured')continue;
    const html=fs.readFileSync(item.page_file,'utf8');
    for(const width of [320,390,768,1320]){
      const page=await browser.newPage({viewport:{width,height:840},deviceScaleFactor:1});
      const errors=[];
      page.on('pageerror',e=>errors.push(e.name));
      await page.route('**/*',route=>route.abort());
      await page.setContent(html,{waitUntil:'load'});
      const m=await page.evaluate(()=>{
        const w=document.documentElement.clientWidth;
        const heads=[...document.querySelectorAll('article h2')];
        const boxes=heads.map(h=>h.getBoundingClientRect());
        const fontSize=Math.min(...heads.map(h=>parseFloat(getComputedStyle(h).fontSize)));
        return {viewport:w,scrollWidth:document.documentElement.scrollWidth,
          lang:document.documentElement.lang,dir:document.documentElement.dir,
          titleCount:heads.length,fontSize,
          titlesInside:boxes.every(b=>b.left>=-1&&b.right<=w+1&&b.height>0),
          textNotClipped:heads.every(h=>h.scrollHeight<=h.clientHeight+2),
          safeLinks:[...document.querySelectorAll('article a')].every(a=>a.protocol==='https:'),
          hasContent:!!document.querySelector('header h1')?.textContent.trim()};
      });
      const langOK=product==='arabic'?(m.lang==='ar'&&m.dir==='rtl'):(m.lang==='en'&&m.dir==='ltr');
      const pass=langOK&&m.scrollWidth<=m.viewport+1&&m.titleCount===item.headlines_shown&&
         m.fontSize>=22&&m.titlesInside&&m.textNotClipped&&m.safeLinks&&m.hasContent&&errors.length===0;
      output.results.push({product,width,passed:pass,metrics:m,script_errors:errors.length});
      if(width===390)await page.screenshot({path:path.join(record.temp_dir,product+'-390.png'),fullPage:true});
      await page.close();
    }
  }
  output.passed=output.results.length===8&&output.results.every(r=>r.passed);
  fs.mkdirSync('reports/v2-b37',{recursive:true});
  fs.writeFileSync('reports/v2-b37/mobile-qa-metadata.json',JSON.stringify(output,null,2)+'\n');
  process.stdout.write(JSON.stringify({schema:output.schema,passed:output.passed,
    source_status:output.source_status,viewport_pass:output.results.map(r=>({product:r.product,width:r.width,passed:r.passed}))})+'\n');
  if(!output.passed)process.exitCode=1;
}finally{await browser.close();}
