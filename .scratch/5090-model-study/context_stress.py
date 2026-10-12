#!/usr/bin/env python3
"""Seeded multi-key retrieval amid unique distractors; token-counted, cold prefixes."""
import argparse,sys,runpy,pathlib,json,random,urllib.request
p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=18000);p.add_argument('--container',default='');p.add_argument('--label',required=True);p.add_argument('--sizes',required=True);p.add_argument('--seeds',default='1,2');p.add_argument('--llama',action='store_true');p.add_argument('--timeout',type=int,default=900);a=p.parse_args()
sys.argv=['benchmark.py','--port',str(a.port),'--container',a.container,'--label',a.label,'--timeout',str(a.timeout),'--out',str(pathlib.Path(__file__).parent/'results')]+(['--llama'] if a.llama else [])
b=runpy.run_path(str(pathlib.Path(__file__).with_name('benchmark.py')))
base=b['base'];headers=b['headers']
def post(path,body):
 req=urllib.request.Request(base+path,data=json.dumps(body).encode(),headers=headers)
 return json.load(urllib.request.urlopen(req,timeout=180))
def count(prompt):
 body={'model':b['model'],'messages':b['chat'](prompt),'add_generation_prompt':True,'chat_template_kwargs':{'enable_thinking':False}}
 if a.llama:body={'content':post('/apply-template',body)['prompt'],'add_special':True}
 obj=post('/tokenize',body)
 return obj.get('count',len(obj.get('tokens',[])))
for size in map(int,a.sizes.split(',')):
 for seed in map(int,a.seeds.split(',')):
  rng=random.Random(seed+size); expected={k:rng.randbytes(6).hex().upper() for k in ('TARGET_A','TARGET_B','TARGET_C')};expected['ABSENT_KEY']='UNKNOWN'
  n=max(4,size//32)
  def make(n):
   rr=random.Random(seed+size+90000)
   lines=[f'ID_{i:07d}: token={rr.randbytes(8).hex()}; status={rr.choice(["queued","ready","done","paused"])}; owner=worker_{rr.randrange(1000)}.\n' for i in range(n)]
   for k,depth in zip(('TARGET_A','TARGET_B','TARGET_C'),(.1,.5,.9)):
    lines.insert(int(n*depth),f'{k}: token={expected[k]}; status=verified.\n')
   return f'Archive batch {size}-{seed}. Extract exact token fields for TARGET_A, TARGET_B, TARGET_C and ABSENT_KEY. If absent use UNKNOWN. Return only a JSON object mapping these four names to token strings.\n'+''.join(lines)+'\nNow output the four requested fields as JSON.'
  try:
   for _ in range(4):
    prompt=make(n);tokens=count(prompt)
    if abs(tokens-(size-512))<64:break
    n=max(4,int(n*(size-512)/tokens))
   prompt=make(n);tokens=count(prompt)
   r=b['request'](f'stress_{size}_seed{seed}',b['chat'](prompt),max_tokens=128)
   try:actual=json.loads(r['text']);passed=actual==expected
   except Exception:passed=False
   r.update(passed=passed,retrieved_all=all(value in r.get('text','') for value in expected.values()),expected=expected,tokenized_prompt=tokens,target_context=size,seed=seed)
  except Exception as e:r={'name':f'stress_{size}_seed{seed}','label':a.label,'error':str(e),'passed':False}
  b['save'](r)
