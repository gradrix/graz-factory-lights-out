#!/usr/bin/env python3
"""Synthetic local-model qualification. No repository/private data sent to models."""
import argparse,json,time,urllib.request,urllib.error,subprocess,pathlib,re,statistics,hashlib
p=argparse.ArgumentParser(); p.add_argument('--port',type=int,default=8000);p.add_argument('--container',default='local-vllm');p.add_argument('--label',required=True);p.add_argument('--out',default='results');p.add_argument('--contexts',default='');p.add_argument('--quality',action='store_true');p.add_argument('--llama',action='store_true');p.add_argument('--agents',action='store_true');p.add_argument('--thinking',action='store_true');p.add_argument('--timeout',type=int,default=900);p.add_argument('--speed',action='store_true');a=p.parse_args()
out=pathlib.Path(a.out);out.mkdir(parents=True,exist_ok=True)
key=''
if a.container:
 c=json.loads(subprocess.check_output(['docker','inspect',a.container]))[0]
 key=dict(x.split('=',1) for x in c['Config']['Env'] if '=' in x).get('VLLM_API_KEY','')
base=f'http://127.0.0.1:{a.port}'
headers={'Content-Type':'application/json','Authorization':'Bearer '+key}
def get(path):return json.load(urllib.request.urlopen(urllib.request.Request(base+path,headers=headers),timeout=30))
model=get('/v1/models')['data'][0]['id']
def request(name,messages,**kw):
 body=dict(model=model,messages=messages,temperature=0,max_tokens=768,stream=True,stream_options={'include_usage':True},chat_template_kwargs={'enable_thinking':False});body.update(kw)
 if a.thinking:body.update(reasoning_effort="medium",chat_template_kwargs={"enable_thinking":True,"reasoning_effort":"medium"})
 if a.llama:body.setdefault("reasoning_effort","none")
 start=time.monotonic(); first=None;text='';reason='';usage={};calls={};finish=None
 result=dict(name=name,label=a.label,model=model,request=body)
 try:
  req=urllib.request.Request(base+'/v1/chat/completions',data=json.dumps(body).encode(),headers=headers)
  with urllib.request.urlopen(req,timeout=a.timeout) as f:
   for line in f:
    if not line.startswith(b'data: '):continue
    if line.strip()==b'data: [DONE]':break
    obj=json.loads(line[6:]);usage=obj.get('usage') or usage
    for choice in obj.get('choices',[]):
     d=choice.get('delta',{});finish=choice.get('finish_reason') or finish
     if any(d.get(k) for k in ('content','reasoning','reasoning_content','tool_calls')) and first is None:first=time.monotonic()
     text+=d.get('content') or '';reason+=d.get('reasoning_content') or d.get('reasoning') or ''
     for tc in d.get('tool_calls',[]):
      t=calls.setdefault(tc['index'],{'id':'','type':'function','function':{'name':'','arguments':''}})
      if tc.get('id'):t['id']=tc['id']
      for k in ('name','arguments'):t['function'][k]+=tc.get('function',{}).get(k) or ''
  elapsed=time.monotonic()-start;tokens=usage.get('completion_tokens',0)
  result.update(text=text,reasoning=reason,tool_calls=list(calls.values()),usage=usage,finish_reason=finish,elapsed_s=elapsed,ttft_s=None if first is None else first-start,decode_tokens_s=(tokens-1)/(time.monotonic()-first) if first and tokens>1 else None)
 except urllib.error.HTTPError as e:result.update(error=str(e),http_status=e.code,error_body=e.read().decode(errors='replace')[:4000],elapsed_s=time.monotonic()-start)
 except Exception as e:result.update(error=str(e),elapsed_s=time.monotonic()-start)
 return result

def save(r):
 # Keep actual prompts in raw artifacts so the experiment is reproducible.
 with (out/(a.label+'.jsonl')).open('a') as f:f.write(json.dumps(r)+'\n')
 print(json.dumps({k:v for k,v in r.items() if k not in ('request','text','reasoning','tool_calls')}),flush=True)

def cleanup_grading():
 ids=subprocess.check_output(['docker','ps','-q','--filter','label=benchmark-5090-grading=true'],text=True).split()
 if ids:subprocess.run(['docker','rm','-f']+ids,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
def chat(s):return [{'role':'user','content':s}]
if a.speed:
 for i in range(3):
  r=request(f'speed_{i}',chat(f'Experiment {i}: list integers from 1 to 400, one per line. Do not stop early.'),max_tokens=256);save(r)
TASKS=[
('merge_intervals','Implement merge_intervals(xs): merge overlapping OR touching closed numeric intervals; return sorted list of tuples; do not mutate input.',"assert merge_intervals([(5,7),(1,3),(3,5),(10,11)])==[(1,7),(10,11)]\nassert merge_intervals([])==[]\nx=[(2,4),(1,2)]; merge_intervals(x); assert x==[(2,4),(1,2)]"),
('toposort','Implement topo(nodes, edges): lexicographically smallest topological order; edges are (prerequisite, dependent); ignore duplicate edges; raise ValueError for cycles. All nodes are strings and present in nodes.',"assert topo(['c','a','b','d'],[('a','c'),('b','c'),('a','c')])==['a','b','c','d']\nassert topo([],[])==[]\ntry: topo(['a','b'],[('a','b'),('b','a')])\nexcept ValueError: pass\nelse: raise AssertionError('cycle')"),
('ttl','Implement class Cache: put(key,value,now,ttl); get(key,now) returns value or None. expires at now>=insertion_time+ttl. Overwrites reset expiry, ttl<=0 expires immediately. No real clock.',"c=Cache();c.put('a',0,10,3);assert c.get('a',12)==0;assert c.get('a',13) is None\nc.put('x',1,20,5);c.put('x',2,22,10);assert c.get('x',26)==2;assert c.get('x',32) is None\nc.put('z',3,0,0);assert c.get('z',0) is None"),
('json_merge','Implement merge_patch(target, patch) per RFC7396: non-dict patch replaces target, dict patch recursively merges into a copied dict target or empty dict; null values delete keys. Do not mutate either input.',"a={'a':{'b':1,'c':2},'d':[1]};p={'a':{'b':None,'x':4},'d':[2]};r=merge_patch(a,p);assert r=={'a':{'c':2,'x':4},'d':[2]};assert a['a']['b']==1;assert p['a']['b'] is None\nassert merge_patch([1],{'x':1})=={'x':1}\nassert merge_patch({'a':1},None) is None"),
('csv','Implement parse_csv(text): parse comma-separated records supporting quoted fields, doubled quotes, embedded newline, LF or CRLF record separators. Return list of lists. Empty input returns []; trailing record newline adds no empty record. Standard library allowed.',"assert parse_csv('')==[]\nassert parse_csv('a,b\\r\\n\"c,d\",\"e\"\"f\"\\r\\n')==[['a','b'],['c,d','e\"f']]\nassert parse_csv('\"a\\nb\",c\\n')==[['a\\nb','c']]"),
('retry','Implement retry(fn, attempts, retryable): call fn at most attempts times, return first success. Catch only exception classes in retryable tuple; propagate last error on exhaustion; attempts<1 raises ValueError before calling fn.',"n=[0]\ndef f():\n n[0]+=1\n if n[0]<3:raise OSError('x')\n return 9\nassert retry(f,3,(OSError,))==9 and n[0]==3\ntry:retry(lambda:1,0,(OSError,))\nexcept ValueError:pass\nelse:raise AssertionError()"),
('version','Implement cmp_version(a,b): dot-separated nonnegative integer version strings; missing trailing components are zero; return -1,0,1. Compare numerically, no float conversion.',"assert cmp_version('1.10','1.9')==1\nassert cmp_version('1','1.0.0')==0\nassert cmp_version('2.0','10')==-1\nassert cmp_version('0001.002','1.2')==0"),
('window','Implement longest_unique(s): length of longest contiguous substring with no repeated characters; Unicode characters count as single characters; O(n) time.',"assert longest_unique('abcabcbb')==3\nassert longest_unique('abba')==2\nassert longest_unique('')==0\nassert longest_unique('😀a😀bc')==4\nassert longest_unique('a'*100000)==1"),
]
if a.quality:
 for name,prompt,tests in TASKS:
  r=request(name,chat(prompt+' Return only Python code, no explanation.'))
  if 'error' not in r:
   code=r['text'];m=re.search(r'```(?:python)?\s*\n(.*?)```',code,re.S);code=m.group(1) if m else code
   try:
    proc=subprocess.run(['docker','run','--rm','--label','benchmark-5090-grading=true','-i','--network','none','--memory','128m','--cpus','1','--pids-limit','32','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges','python@sha256:ae52c5bef62a6bdd42cd1e8dffef86b9cd284bde9427da79839de7a4b983e7ca','python','-I','-'],input=code+'\n'+tests,text=True,capture_output=True,timeout=20)
    r.update(passed=proc.returncode==0,grade_output=(proc.stdout+proc.stderr)[-2000:])
   except subprocess.TimeoutExpired:
    cleanup_grading();r.update(passed=False,grade_output='20s sandbox timeout')
  save(r)
 tool={'type':'function','function':{'name':'lookup_weather','description':'Look up weather for a city on an ISO date','parameters':{'type':'object','properties':{'city':{'type':'string'},'date':{'type':'string'}},'required':['city','date'],'additionalProperties':False}}}
 for city,date in [('Vilnius','2026-10-01'),('New York','2026-12-31'),('São Paulo','2027-01-02')]:
  r=request('tool_'+city,chat(f'Use lookup_weather to get weather for {city} on {date}.'),tools=[tool],tool_choice='auto',max_tokens=256)
  try:t=r['tool_calls'];r['passed']=len(t)==1 and t[0]['function']['name']=='lookup_weather' and json.loads(t[0]['function']['arguments'])=={'city':city,'date':date}
  except Exception:r['passed']=False
  save(r)
 r=request('json',chat('Return only JSON with keys names and sum. names is the alphabetically sorted unique names from ["Zoe","Ana","Zoe","Bo"]. sum is the sum of [17,-5,22,-4].'),max_tokens=128)
 try:r['passed']=json.loads(r['text'])=={'names':['Ana','Bo','Zoe'],'sum':30}
 except Exception:r['passed']=False
 save(r)
if a.contexts:
 # Filler tokens calibrated with the actual server tokenizer; records contain independent keys.
 for target in map(int,a.contexts.split(',')):
  needle='the immutable launch code is RIVER-7291-OLIVE'; filler='Ordinary archive entry. Nothing here changes the launch code.\n'
  def prompt(n):
   parts=[filler]*(n);parts.insert(n//10,needle+'\n');parts.insert(n//2,'Archive note: secondary marker is AMBER-4816.\n');parts.insert(9*n//10,'Archive note: final marker is CEDAR-9352.\n')
   return 'Read the archive and remember its three markers.\n'+''.join(parts)+'\nReturn only the launch code, secondary marker, and final marker, in that order.'
  n=max(1,target//12)
  try:
   for _ in range(3):
    tokbody={'model':model,'messages':chat(prompt(n)),'add_generation_prompt':True,'chat_template_kwargs':{'enable_thinking':False}}
    if a.llama:
     req=urllib.request.Request(base+'/apply-template',data=json.dumps(tokbody).encode(),headers=headers)
     rendered=json.load(urllib.request.urlopen(req,timeout=90))['prompt']
     tokbody={'content':rendered,'add_special':True}
    req=urllib.request.Request(base+'/tokenize',data=json.dumps(tokbody).encode(),headers=headers)
    obj=json.load(urllib.request.urlopen(req,timeout=90));count=obj.get('count',len(obj.get('tokens',[])))
    if not count:raise ValueError('no token count')
    n=max(1,int(n*(target-256)/count))
   r=request('context_'+str(target),chat(prompt(n)),max_tokens=128)
   r['target_context']=target;r['passed']=all(x in r.get('text','') for x in ('RIVER-7291-OLIVE','AMBER-4816','CEDAR-9352'));save(r)
  except Exception as e:save({'label':a.label,'name':'context_'+str(target),'error':str(e)})
if a.agents:
 tools=[{'type':'function','function':{'name':name,'description':desc,'parameters':{'type':'object','properties':props,'required':list(props),'additionalProperties':False}}} for name,desc,props in [
 ('read_file','Read the sole project file app.py',{'path':{'type':'string'}}),
 ('write_file','Replace the full contents of app.py',{'path':{'type':'string'},'content':{'type':'string'}}),
 ('run_tests','Run the project acceptance tests',{})]]
 cases=[('repair_expiry','Fix the cache: entries must expire at the deadline, overwrites must replace old deadlines, and cached false/zero values must survive. Inspect the file, make the fix, run tests, then summarize.',
 "class Cache:\n    def __init__(self): self.data = {}\n    def put(self, key, value, now, ttl):\n        if key not in self.data: self.data[key] = (value, now + ttl)\n    def get(self, key, now):\n        entry = self.data.get(key)\n        if not entry or now > entry[1]: return None\n        return entry[0] or None\n",
 TASKS[2][2]+"\nc=Cache();c.put('f',False,0,5);assert c.get('f',4) is False\n"),
 ('repair_events','Fix apply_event(state,event). state maps id to {version,value}. Ignore events whose version is not strictly greater than stored version; unseen IDs accept any integer version. Return a new state without mutating either input. Inspect, edit, run tests, then summarize.',
 "def apply_event(state, event):\n    key = event['id']\n    current = state.get(key)\n    if current and event['version'] < current['version']:\n        return state\n    state[key] = {'version': event['version'], 'value': event['value']}\n    return state\n",
 "s={'a':{'version':2,'value':'old'}}\nr=apply_event(s,{'id':'a','version':2,'value':'duplicate'});assert r==s\nr=apply_event(s,{'id':'a','version':3,'value':'new'});assert r['a']['value']=='new';assert s['a']['value']=='old'\nassert apply_event({}, {'id':'x','version':-2,'value':0})=={'x':{'version':-2,'value':0}}\nr['a']['value']='changed';assert s['a']['value']=='old'\n")]
 for name,prompt,code,tests in cases:
  messages=[{'role':'system','content':'You are fixing a tiny Python project. Use the available file and test tools. Only app.py exists. Finish after tests pass.'}]+chat(prompt)
  passed=False;seen=set();records=[]
  for turn in range(7):
   r=request(name+'_turn_'+str(turn),messages,tools=tools,tool_choice='auto',max_tokens=4096 if a.thinking else 1024)
   records.append(r);save(r)
   if 'error' in r:break
   calls=r.get('tool_calls',[])
   if not calls:break
   messages.append({'role':'assistant','content':r.get('text') or None,'tool_calls':calls})
   for tc in calls:
    fn=tc['function']['name'];seen.add(fn)
    try:
     args=json.loads(tc['function']['arguments'])
     if fn in ('read_file','write_file') and args.get('path')!='app.py':raise ValueError('only app.py exists')
     if fn=='read_file':response=code
     elif fn=='write_file':code=args['content'];passed=False;response='written'
     elif fn=='run_tests':
      proc=subprocess.run(['docker','run','--rm','--label','benchmark-5090-grading=true','-i','--network','none','--memory','128m','--cpus','1','--pids-limit','32','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges','python@sha256:ae52c5bef62a6bdd42cd1e8dffef86b9cd284bde9427da79839de7a4b983e7ca','python','-I','-'],input=code+'\n'+tests,text=True,capture_output=True,timeout=20)
      passed=proc.returncode==0;response='All tests passed' if passed else (proc.stdout+proc.stderr)[-1800:]
     else:response='unknown tool'
    except Exception as e:
     if isinstance(e,subprocess.TimeoutExpired):cleanup_grading()
     response='Tool error: '+str(e)
    messages.append({'role':'tool','tool_call_id':tc['id'],'content':response})
  save({'name':name+'_summary','label':a.label,'passed':passed and seen=={'read_file','write_file','run_tests'},'turns':len(records),'tools_seen':sorted(seen),'elapsed_s':sum(r['elapsed_s'] for r in records),'final_code':code})
