#!/usr/bin/env python3
"""Temporary, loopback-only comparison servers. Original container is retained."""
import argparse,json,pathlib,subprocess,time,urllib.request
p=argparse.ArgumentParser();p.add_argument('action',choices=['vllm','bonsai','qwen','flash','restore']);p.add_argument('--context',type=int,default=32768);p.add_argument('--cache',default='f16');p.add_argument('--scale',type=float,default=1);p.add_argument('--memory',default='0.92');p.add_argument('--graphs',action='store_true');p.add_argument('--layers',default='99');p.add_argument('--batch',default='256');p.add_argument('--kv-bytes',type=int);a=p.parse_args()
if a.action in ('bonsai','qwen','flash') and a.context>262144 and a.scale==1:p.error('Beyond native 262144 context requires an explicit experimental --scale setting.')
root=pathlib.Path.home()/'benchmark-5090';original=json.loads((root/'original-container.private.json').read_text());name='benchmark-5090-server'
def run(cmd,**kw):return subprocess.run(cmd,check=True,**kw)
existing=subprocess.run(['docker','inspect',name],capture_output=True)
if existing.returncode==0:
 cfg=json.loads(existing.stdout)[0]
 if cfg['Config']['Labels'].get('benchmark-5090')!='true':raise SystemExit('unexpected owner')
 run(['docker','rm','-f',name])
if a.action=='restore':
 run(['docker','start','local-vllm']);raise SystemExit(0)
run(['docker','stop','-t','40','local-vllm'])
cmd=['docker','run','-d','--name',name,'--label','benchmark-5090=true','--gpus','all','--shm-size','8g','-p','127.0.0.1:18000:8000']
if a.action=='vllm':
 env=root/'vllm-test.private.env';env.touch(mode=0o600);env.write_text('\n'.join(original['Config']['Env'])+'\n');env.chmod(0o600)
 cmd+=['--env-file',str(env)]
 for m in original['Mounts']:cmd+=['-v',m['Name']+':'+m['Destination']]
 args=original['Config']['Cmd'].copy()
 for flag,value in [('--max-model-len',str(a.context)),('--max-num-seqs','1'),('--gpu-memory-utilization',a.memory)]:
  if flag in args:args[args.index(flag)+1]=value
  else:args +=[flag,value]
 if a.kv_bytes:args+=['--kv-cache-memory-bytes',str(a.kv_bytes)]
 if a.graphs:
  args=[x for x in args if x!='--enforce-eager']
  args+=['--max-num-batched-tokens','2048','--compilation-config',json.dumps({'cudagraph_mode':'FULL_DECODE_ONLY','cudagraph_capture_sizes':[1],'max_cudagraph_capture_size':1})]
 cmd+=[original['Image']]+args
else:
 binary='/study/bonsai/llama-prism-b10743-adfffbe/llama-server'
 model='/study/bonsai/Ternary-Bonsai-2-27B-PQ2_0.gguf' if a.action=='bonsai' else '/study/qwen/Qwen3.8-27B-UD-Q4_K_M.gguf'
 if a.action=='flash':
  binaries=list((root/'flash'/'runtime').rglob('llama-server'))
  if len(binaries)!=1:raise SystemExit('expected one Flash runtime')
  binary='/study/'+str(binaries[0].relative_to(root))
  model='/study/flash/Qwen3.8-Flash-Next-GSQ-RCO-IQ1_M-00001-of-00002.gguf'
 cmd+=['-v',str(root)+':/study:ro','--entrypoint',binary,original['Image'],'--model',model,'--alias',('flash-next-coder' if a.action=='flash' else a.action+'-27b'),'--host','0.0.0.0','--port','8000','-ngl',a.layers,'-fa','on','-c',str(a.context),'-np','1','--cache-type-k',a.cache,'--cache-type-v',a.cache,'--reasoning','auto','--jinja','--fit','off']
 if a.action=='flash':cmd+=['-b',a.batch,'-ub',a.batch,'-lm','mmap','--lazy-mode','on']
 if a.scale!=1:cmd+=['--rope-scaling','yarn','--rope-scale',str(a.scale),'--yarn-orig-ctx','262144','--override-kv',('qwen4exp' if a.action=='flash' else 'qwen35')+'.context_length=int:'+str(a.context)]
label=f'{a.action}-{a.context}-'+('fp8' if a.action=='vllm' else a.cache)+('-graphs' if a.graphs else '')+('-b'+a.batch+'-ngl'+a.layers if a.action=='flash' else '')+('-yarn'+str(a.scale) if a.scale!=1 else '')+('-kv'+str(a.kv_bytes) if a.kv_bytes else '')
(root/(label+'-launch.json')).write_text(json.dumps({'command':cmd,'date':time.strftime('%Y-%m-%dT%H:%M:%S%z')},indent=2))
run(cmd)
for i in range(180):
 state=json.loads(subprocess.check_output(['docker','inspect',name]))[0]['State']
 if not state['Running']:
  print(subprocess.check_output(['docker','logs',name],stderr=subprocess.STDOUT,text=True)[-6000:]);raise SystemExit('server exited')
 try:
  req=urllib.request.Request('http://127.0.0.1:18000/health')
  with urllib.request.urlopen(req,timeout=2) as f:
   if f.status==200:
    print('HTTP_READY '+label,flush=True);break
 except Exception:pass
 time.sleep(2)
else:raise SystemExit('readiness timeout; use profiles.py restore')
(root/(label+'-startup.log')).write_text(subprocess.check_output(['docker','logs',name],stderr=subprocess.STDOUT,text=True))
if a.action!='vllm':
 with urllib.request.urlopen('http://127.0.0.1:18000/props',timeout=10) as response:props=json.load(response)
 actual_ctx=props.get('default_generation_settings',{}).get('n_ctx')
 (root/(label+'-readback.json')).write_text(json.dumps({'requested_context':a.context,'served_context':actual_ctx,'native_context':262144,'experimental_metadata_override':a.scale!=1},indent=2))
 if actual_ctx is None or actual_ctx<a.context:raise SystemExit('Server context is capped; inspect readback and startup log')
print('READY '+label,flush=True)
memory=subprocess.check_output(['/usr/lib/wsl/lib/nvidia-smi','--query-gpu=memory.used,memory.total','--format=csv'],text=True)
(root/(label+'-memory.txt')).write_text(memory)
print(memory)
