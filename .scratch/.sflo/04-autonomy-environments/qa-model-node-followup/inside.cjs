const fs=require('fs'),cp=require('child_process'),assert=require('assert/strict');
const root='/tmp/relocated project';fs.cpSync('/source',root,{recursive:true,filter:p=>!['.git','dist'].includes(require('path').basename(p))});
cp.execFileSync('node',['/node_modules/typescript/bin/tsc','-p','./tsconfig.json'],{cwd:root,stdio:'inherit'});
cp.execFileSync('node',['--test','tests/availability.test.js'],{cwd:root,stdio:'inherit'});
cp.execFileSync('node',['--test'],{cwd:root,stdio:'inherit'});
const example=cp.execFileSync('sh',['-c',`echo '{"action":"availability","window":{"start":0,"end":100},"busy":[{"start":10,"end":30}],"minDuration":5}' | node dist/cli.js`],{cwd:root,encoding:'utf8'});assert.deepStrictEqual(JSON.parse(example),[{start:0,end:10,duration:10},{start:30,end:100,duration:70}]);
const {dispatch}=require(root+'/dist/api.js');let seed=8821;const rng=n=>{seed=(Math.imul(seed,1103515245)+12345)>>>0;return seed%n};
function freeze(x){if(x&&typeof x==='object'){Object.values(x).forEach(freeze);Object.freeze(x)}return x;}
for(let i=0;i<150;i++){
 const start=rng(10),end=10+rng(20),busy=Array.from({length:rng(16)},()=>{const a=rng(35);return {start:a,end:a+1+rng(10)}}),minDuration=1+rng(10),p={action:'availability',window:{start,end},busy,minDuration},want=[];
 const free=Array.from({length:end-start},(_,k)=>start+k).filter(t=>!busy.some(b=>b.start<=t&&t<b.end));let a=null,last=null;
 for(const t of [...free,Infinity]){if(a!==null&&t!==last+1){if(last+1-a>=minDuration)want.push({start:a,end:last+1,duration:last+1-a});a=null}if(t!==Infinity){if(a===null)a=t;last=t}}
 const before=structuredClone(p);assert.deepStrictEqual(dispatch(freeze(p)),want);assert.deepStrictEqual(p,before);
 if(i<10){const r=cp.spawnSync('node',[root+'/dist/cli.js'],{cwd:'/tmp',input:JSON.stringify(p),encoding:'utf8'});assert.equal(r.status,0);assert.deepStrictEqual(JSON.parse(r.stdout),want)}
}
const base={action:'availability',window:{start:10,end:20},busy:[],minDuration:1};let count=0;
for(const busy of [[{start:-1,end:0}],[{start:30,end:1000001}],[{start:1,end:1.5}],[{end:8}],[{start:NaN,end:8}],[{start:30,end:Infinity}],Array(1)]){const p={...base,busy},before=structuredClone(p);assert.throws(()=>dispatch(freeze(p)),Error);assert.deepStrictEqual(p,before);count++}
console.log(JSON.stringify({random_cases:150,CLI_cases:10,frozen_invalid_cases:count,documented_commands:true,node:process.version}));
