const fs=require('fs'),net=require('net'),assert=require('assert/strict');
const {chromium}=require('/probe/node_modules/playwright');
function emit(name,data){console.log(JSON.stringify({name,data}));}
async function denied(host,port){return new Promise(resolve=>{const s=net.connect({host,port});s.setTimeout(1500);s.once('connect',()=>{s.destroy();resolve({host,port,connected:true})});s.once('error',e=>resolve({host,port,error:e.code,connected:false}));s.once('timeout',()=>{s.destroy();resolve({host,port,error:'timeout',connected:false})});});}
(async()=>{
 emit('identity',{uid:process.getuid(),node:process.version,playwright:require('/probe/node_modules/playwright/package.json').version,route:fs.readFileSync('/proc/net/route','utf8'),interfaces:fs.readFileSync('/proc/net/dev','utf8'),status:fs.readFileSync('/proc/self/status','utf8').split('\n').filter(x=>/^(Cap|NoNewPrivs|Seccomp)/.test(x)),gpuDevices:fs.readdirSync('/dev').filter(x=>/nvidia|dri/.test(x)),dockerSocket:fs.existsSync('/var/run/docker.sock')});
 const response=await fetch('http://127.0.0.1:3210');assert.equal(response.status,200);emit('app-http',{status:response.status});
 for(const [host,port] of [['172.17.0.1',80],['10.1.1.155',22],['1.1.1.1',443],['2606:4700:4700::1111',443]]){const result=await denied(host,port);emit('network-denial',result);assert.equal(result.connected,false);}
 let browser;
 try{browser=await chromium.launch({headless:true,chromiumSandbox:true,timeout:20000});emit('browser-version',browser.version());const context=await browser.newContext({serviceWorkers:'block'});const page=await context.newPage();await page.goto('http://127.0.0.1:3210');await page.locator('#increment').click();assert.equal(await page.locator('#count').textContent(),'1');emit('journey',{title:await page.title(),count:await page.locator('#count').textContent()});
 const read=(p)=>{try{return fs.readFileSync(p,'utf8')}catch(e){return {error:e.code}}};
 const link=(p)=>{try{return fs.readlinkSync(p)}catch(e){return {error:e.code}}};
 const procs=[];for(const p of fs.readdirSync('/proc').filter(x=>/^\d+$/.test(x))){const cmd=read('/proc/'+p+'/cmdline');if(typeof cmd==='string' && /chrome|chromium/.test(cmd)){const status=read('/proc/'+p+'/status');procs.push({pid:p,cmd:cmd.replaceAll('\0',' '),status:typeof status==='string'?status.split('\n').filter(x=>/^(Name|Pid|PPid|NSpid|Uid|Gid|Cap|NoNewPrivs|Seccomp)/.test(x)):status,uid_map:read('/proc/'+p+'/uid_map'),gid_map:read('/proc/'+p+'/gid_map'),namespaces:Object.fromEntries(['user','pid','net','mnt'].map(n=>[n,link('/proc/'+p+'/ns/'+n)]))})}}emit('browser-processes',procs);emit('reporter-namespaces',{uid_map:read('/proc/self/uid_map'),namespaces:Object.fromEntries(['user','pid','net','mnt'].map(n=>[n,link('/proc/self/ns/'+n)]))});assert.ok(procs.every(p=>!p.cmd.includes('--no-sandbox')));assert.ok(procs.some(p=>p.cmd.includes('--type=renderer')));
 await browser.close();emit('result','PASS');}
 catch(e){emit('sandbox-failure',String(e).slice(0,10000));if(browser)await browser.close();process.exitCode=1;}
})().catch(e=>{emit('fatal',String(e));process.exitCode=1;});
