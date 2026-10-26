/** B32 local Playwright QA. No network, model, webhook or publication. */
import fs from 'node:fs';
import { createRequire } from 'node:module';
import { execFileSync } from 'node:child_process';
import path from 'node:path';
const require = createRequire(import.meta.url);
const { chromium } = require('playwright');

const fixture = JSON.parse(execFileSync('python3', ['-B', 'v2_b32_generate_mobile_fixtures.py'], {
  cwd: process.cwd(), encoding: 'utf8', timeout: 15000,
}));
const output = {schema:'aggregateit-v2-b32-emulated-browser-qa/1',
  browser:'Chromium', emulated_viewports:true, actual_phone_verified:false,
  fixture_sha256:Object.fromEntries(Object.entries(fixture.products).map(([key,row])=>[key,row.sha256])),
  network_requests_allowed:false, runs:[], passed:false, discord_sent:false};

const browser = await chromium.launch({headless:true, args:['--no-sandbox']});
try {
  for(const [product, info] of Object.entries(fixture.products)) {
    const html = fs.readFileSync(info.path,'utf8');
    for(const width of [320,390,768,1320]) {
      const page = await browser.newPage({viewport:{width,height:860}, deviceScaleFactor:1});
      const consoleErrors=[];
      page.on('pageerror',e=>consoleErrors.push(e.message));
      await page.route('**/*',route=>route.abort());
      await page.setContent(html,{waitUntil:'load'});
      const metrics=await page.evaluate(()=>{
        const viewport=document.documentElement.clientWidth;
        const main=document.querySelector('main')?.getBoundingClientRect();
        const cards=[...document.querySelectorAll('article')];
        const bounds=cards.map(c=>c.getBoundingClientRect());
        return { viewport, scrollWidth:document.documentElement.scrollWidth,
          lang:document.documentElement.lang, dir:document.documentElement.dir,
          cardCount:cards.length, titleVisible:!!document.querySelector('h1')?.textContent?.trim(),
          cardsWithinViewport:bounds.every(r=>r.left>=-1 && r.right<=viewport+1 && r.width>0),
          mainWithinViewport:!!main && main.left>=-1 && main.right<=viewport+1};
      });
      const correctLanguage=(product==='arabic' ? metrics.lang==='ar' && metrics.dir==='rtl'
                                                : metrics.lang==='en' && metrics.dir==='ltr');
      const passed=correctLanguage && metrics.scrollWidth<=metrics.viewport+1 &&
         metrics.cardCount===info.expected_stories && metrics.titleVisible &&
         metrics.cardsWithinViewport && metrics.mainWithinViewport && consoleErrors.length===0;
      if(width===390 || width===1320) {
        await page.screenshot({path:path.join(fixture.output_dir,`${product}-${width}.png`),fullPage:true});
      }
      output.runs.push({product,width,metrics,consoleErrors,passed});
      await page.close();
    }
  }
  output.passed=output.runs.length===8 && output.runs.every(row=>row.passed);
  output.output_dir=fixture.output_dir;
  fs.writeFileSync(path.join(fixture.output_dir,'qa-report.json'),JSON.stringify(output,null,2)+'\n');
  process.stdout.write(JSON.stringify(output)+'\n');
  if(!output.passed)process.exitCode=1;
} finally {
  await browser.close();
}
