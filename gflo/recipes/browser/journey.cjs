'use strict';
const fs=require('fs'),crypto=require('crypto'),net=require('net');
const {chromium}=require('/support/playwright');
const baseURL='http://127.0.0.1:3210';
const output='/tmp/evidence';fs.mkdirSync(output);
const events=[],contexts=[],files=[];let contextSlots=0;let browser,phase='readiness',failure=null,shots=0,eventBytes=2;
const start=Date.now();const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const deadline=(promise,ms,label)=>new Promise((resolve,reject)=>{const timer=setTimeout(()=>reject(new Error(label+' deadline')),ms);promise.then(v=>{clearTimeout(timer);resolve(v)},e=>{clearTimeout(timer);reject(e)})});
function event(kind,value){const e={kind,value:String(value).slice(0,1024)};eventBytes+=Buffer.byteLength(JSON.stringify(e))+1;if(events.length>=512||eventBytes>256*1024)throw new Error('Browser event limit');events.push(e);}
function fail(error){if(!failure)failure={phase,message:String(error).slice(0,4096)};}
function allowed(url){try{const value=new URL(url);return value.origin===baseURL&&!value.username&&!value.password}catch{return false}}
function proc(){const read=p=>{try{return fs.readFileSync(p,'utf8')}catch{return ''}},link=p=>{try{return fs.readlinkSync(p)}catch{return ''}};const rows=[];for(const pid of fs.readdirSync('/proc').filter(p=>/^\d+$/.test(p))){const command=read('/proc/'+pid+'/cmdline').replaceAll('\0',' ');if(/chrome|chromium/.test(command))rows.push({pid,command:command.slice(0,4096),status:read('/proc/'+pid+'/status').split('\n').filter(s=>/^(Uid|Gid|NSpid|Cap|NoNewPrivs|Seccomp)/.test(s)),namespaces:Object.fromEntries(['user','pid','net'].map(n=>[n,link('/proc/'+pid+'/ns/'+n)]))});}return {processes:rows,reporter:Object.fromEntries(['user','pid','net'].map(n=>[n,link('/proc/self/ns/'+n)])),shm:fs.statfsSync('/dev/shm',{bigint:false}),memory:read('/sys/fs/cgroup/memory.current').trim(),memoryPeak:read('/sys/fs/cgroup/memory.peak').trim(),memoryEvents:read('/sys/fs/cgroup/memory.events'),memoryStat:read('/sys/fs/cgroup/memory.stat')};}
async function denial(host,port){return new Promise(resolve=>{const s=net.connect({host,port});s.setTimeout(500);s.once('connect',()=>{s.destroy();resolve({host,connected:true})});s.once('error',e=>resolve({host,connected:false,error:e.code}));s.once('timeout',()=>{s.destroy();resolve({host,connected:false,error:'timeout'})})});}
let peakShm=0,samples=0;
function sample(){const s=fs.statfsSync('/dev/shm');peakShm=Math.max(peakShm,(s.blocks-s.bfree)*s.bsize);samples++;}
// Store already-compressed context traces in one bounded opaque ZIP.
function traceBundle(paths){
 const entries=[];let total=0;
 for(const [index,path] of paths.entries()){
  const size=fs.statSync(path).size;total+=size;
  if(total>16*1024*1024)throw new Error('Combined context trace limit');
  entries.push({name:'context-'+(index+1)+'.zip',data:fs.readFileSync(path)});
 }
 const manifest=entries.map((e,index)=>({context:index+1,name:e.name,size:e.data.length,sha256:hash(e.data)}));
 entries.unshift({name:'manifest.json',data:Buffer.from(JSON.stringify({contexts:manifest}))});
 const local=[],central=[];let offset=0;
 function crc32(data){let crc=0xffffffff;for(const byte of data){crc^=byte;for(let n=0;n<8;n++)crc=(crc>>>1)^((crc&1)?0xedb88320:0)}return (crc^0xffffffff)>>>0}
 for(const entry of entries){
  const name=Buffer.from(entry.name),data=entry.data,crc=crc32(data);
  const header=Buffer.alloc(30);header.writeUInt32LE(0x04034b50,0);header.writeUInt16LE(20,4);header.writeUInt32LE(crc,14);header.writeUInt32LE(data.length,18);header.writeUInt32LE(data.length,22);header.writeUInt16LE(name.length,26);
  local.push(header,name,data);
  const directory=Buffer.alloc(46);directory.writeUInt32LE(0x02014b50,0);directory.writeUInt16LE(20,4);directory.writeUInt16LE(20,6);directory.writeUInt32LE(crc,16);directory.writeUInt32LE(data.length,20);directory.writeUInt32LE(data.length,24);directory.writeUInt16LE(name.length,28);directory.writeUInt32LE(offset,42);central.push(directory,name);
  offset+=header.length+name.length+data.length;
 }
 const directory=Buffer.concat(central),end=Buffer.alloc(22);end.writeUInt32LE(0x06054b50,0);end.writeUInt16LE(entries.length,8);end.writeUInt16LE(entries.length,10);end.writeUInt32LE(directory.length,12);end.writeUInt32LE(offset,16);
 if(offset+directory.length+end.length>16*1024*1024)throw new Error('Combined context trace limit');
 fs.writeFileSync(output+'/trace.zip',Buffer.concat([...local,directory,end]));return manifest;
}
async function newContext(){
 if(contextSlots++>=4)throw new Error('Browser context limit');
 const context=await browser.newContext({viewport:{width:1280,height:800},serviceWorkers:'block',acceptDownloads:false});contexts.push(context);
 context.setDefaultTimeout(5000);context.setDefaultNavigationTimeout(10000);
 await context.tracing.start({screenshots:true,snapshots:true,sources:false});
 await context.route('**/*',async route=>{
  if(!allowed(route.request().url())){fail('Disallowed request '+route.request().url());await route.abort('blockedbyclient');return}
  let response;
  try{
   // continue() lets Chromium follow redirect hops outside the route handler.
   // Fetch exactly one approved-origin response, never a redirect target.
   response=await route.fetch({maxRedirects:0,maxRetries:0,timeout:10000});
   if(response.status()>=300&&response.status()<400){fail('HTTP redirects unsupported');await route.abort('blockedbyclient');return}
   await route.fulfill({response});
  }catch(error){fail(error);await route.abort('failed').catch(()=>{})}
  finally{if(response)await response.dispose()}
 });
 await context.routeWebSocket('**/*',socket=>{fail('WebSockets unsupported');socket.close({code:1008,reason:'WebSockets unsupported'})});
 context.on('page',page=>{
  page.on('console',msg=>{try{event('console:'+msg.type(),msg.text())}catch(e){fail(e)}});
  page.on('pageerror',error=>{try{event('pageerror',error)}catch(e){fail(e)};fail(error)});
  page.on('requestfailed',request=>{try{event('requestfailed',request.url()+': '+JSON.stringify(request.failure()))}catch(e){fail(e)}});
  page.on('response',response=>{if(response.status()>=400){try{event('http',response.status()+' '+response.url())}catch(e){fail(e)}}});
  page.on('popup',popup=>{fail('Unexpected popup');popup.close().catch(()=>{})});
  page.on('download',download=>{fail('Download forbidden');download.cancel().catch(()=>{})});
  page.on('filechooser',()=>fail('File upload forbidden'));
  page.on('framenavigated',frame=>{if(frame.url()!=='about:blank'&&!allowed(frame.url()))fail('Disallowed frame navigation '+frame.url())});
 });
 // Prevent file input interaction and window.open before page scripts run.
 await context.addInitScript(()=>{
  window.open=()=>{throw new Error('Popups forbidden by local browser profile')};
  document.addEventListener('click',e=>{if(e.target instanceof HTMLInputElement&&e.target.type==='file'){e.preventDefault();throw new Error('File uploads forbidden by local browser profile')}},true);
 });
 return context;
}
(async()=>{
 let timer;let runtime={node:process.version,playwright:require('/support/playwright/package.json').version,core:require('/support/playwright-core/package.json').version};
 try{
  if(runtime.node!=='v24.20.0'||runtime.playwright!=='1.63.0'||runtime.core!=='1.63.0')throw new Error('Browser support/runtime mismatch');
  const ready=Date.now()+15000;while(true){try{const r=await fetch(baseURL+'/health',{signal:AbortSignal.timeout(500),redirect:'error'});if(r.ok)break}catch{}if(Date.now()>=ready)throw new Error('Application readiness deadline');await sleep(100)}
  runtime.network={interfaces:fs.readFileSync('/proc/net/dev','utf8'),routes:fs.readFileSync('/proc/net/route','utf8'),denials:[]};
  for(const host of ['172.17.0.1','10.1.1.155','1.1.1.1','2606:4700:4700::1111']){const d=await denial(host,443);runtime.network.denials.push(d);if(d.connected)throw new Error('Network isolation failed');}
  phase='launch';browser=await chromium.launch({headless:true,chromiumSandbox:true,timeout:20000,ignoreDefaultArgs:['--disable-dev-shm-usage']});
  runtime.browser=browser.version();if(runtime.browser!=='153.0.8010.12')throw new Error('Browser version mismatch');
  const context=await newContext();
  const page=await context.newPage();sample();timer=setInterval(sample,50);
  const screenshot=async(target=page)=>{if(++shots>8)throw new Error('Screenshot count limit');const name='screen-'+shots+'.png';await target.screenshot({path:output+'/'+name,fullPage:false,timeout:5000});files.push(name)};
  const journey=require('/checks/journey.cjs');if(typeof journey!=='function')throw new Error('Journey must export one function');
  phase='journey';await deadline(journey({page,context,request:context.request,baseURL,screenshot,newContext}),60000,'Journey');
  if(failure)throw new Error(failure.message);
  if(shots===0)throw new Error('Journey saved no screenshot');
  runtime.isolation=proc();
  const renderer=runtime.isolation.processes.find(p=>p.command.includes('--type=renderer'));
  if(!renderer||runtime.isolation.processes.some(p=>p.command.includes('--no-sandbox')||p.command.includes('--disable-dev-shm-usage')))throw new Error('Required renderer/shared-memory launch unavailable');
 }catch(error){fail(error)}
 finally{
  clearInterval(timer);runtime.shm={peakBytes:peakShm,samples};phase='artifact';
  try{await deadline((async()=>{const traces=[];for(const [index,context] of contexts.entries()){const path=output+'/context-'+(index+1)+'.zip';await context.tracing.stop({path});traces.push(path)}if(traces.length){runtime.traces=traceBundle(traces);files.push('trace.zip')}for(const context of contexts)await context.close();if(browser)await browser.close()})(),15000,'Artifact finalization')}catch(error){fail(error)}
 }
 try{
  fs.writeFileSync(output+'/events.json',JSON.stringify(events));files.push('events.json');
  const manifest=[];let total=0;
  for(const name of files){const st=fs.lstatSync(output+'/'+name);const cap=name==='trace.zip'?16*1024*1024:name==='events.json'?256*1024:2*1024*1024;if(!st.isFile()||st.nlink!==1||st.size>cap)throw new Error('Artifact type/size limit');const data=fs.readFileSync(output+'/'+name);total+=data.length;manifest.push({name,size:data.length,sha256:hash(data)})}
  if(total>24*1024*1024)throw new Error('Total artifact limit');
  const result={status:failure?'failed':'passed',failure,runtime,elapsedMs:Date.now()-start,files:manifest};const header=JSON.stringify(result)+'\n';if(Buffer.byteLength(header)>65536)throw new Error('Artifact metadata limit');process.stdout.write(header);for(const name of files)process.stdout.write(fs.readFileSync(output+'/'+name));
 }catch(error){process.stderr.write(String(error).slice(0,4096));process.exitCode=2}
})().catch(error=>{process.stderr.write(String(error).slice(0,4096));process.exitCode=2});
