import os,pathlib,shutil,subprocess,sys,json,random,copy,time,urllib.request,urllib.error
root=pathlib.Path('/work/project');shutil.copytree('/source',root);cwd=pathlib.Path('/work/unrelated');cwd.mkdir();os.chdir(cwd)
subprocess.run(['pip','wheel','--no-index','--no-deps','--no-build-isolation',str(root)],check=True)
wheel=next(cwd.glob('*.whl'));subprocess.run(['pip','install','--no-index','--no-deps','--target','/work/installed',str(wheel)],check=True)
os.environ['PYTHONPATH']='/work/installed:/opt/deps';sys.path.insert(0,'/work/installed')
subprocess.run(['python','-m','unittest','discover','-s',str(root)],check=True)
from telemetry_usage.domain import usage
rng=random.Random(9102)
def expected(samples,start,end):
 out=[]
 for device in sorted({s['device'] for s in samples}):
  window=sorted([s for s in samples if s['device']==device and start<s['at']<=end],key=lambda s:s['at']);deltas=[];resets=0
  for s in window:
   past=[p for p in samples if p['device']==device and p['at']<s['at']]
   if not past:deltas.append(0);continue
   prev=max(past,key=lambda p:p['at'])['reading'];reset=s['reading']<prev;resets+=reset;deltas.append(s['reading'] if reset else s['reading']-prev)
  if window:out.append({'device':device,'increase':sum(deltas),'resets':resets,'samples':len(window),'last_reading':window[-1]['reading']})
 return {'start':start,'end':end,'devices':out}
payloads=[]
for _ in range(100):
 samples=[{'device':d,'at':t,'reading':rng.randrange(30)} for d in ['猫','a','😀'] for t in rng.sample(range(25),rng.randrange(12))];rng.shuffle(samples);start=rng.randrange(12);end=rng.randrange(start+1,26);before=copy.deepcopy(samples);want=expected(samples,start,end);assert usage(samples,start,end)==want;assert samples==before;payloads.append(({'start':start,'end':end,'samples':samples},want))
proc=subprocess.Popen(['python','-m','uvicorn','telemetry_usage.app:app','--host','127.0.0.1','--port','8000'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
def request(payload):
 req=urllib.request.Request('http://127.0.0.1:8000/telemetry/usage',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'})
 try:r=urllib.request.urlopen(req,timeout=3)
 except urllib.error.HTTPError as e:r=e
 with r:return r.status,json.load(r)
try:
 for _ in range(100):
  try:
   urllib.request.urlopen('http://127.0.0.1:8000/health',timeout=1).close();break
  except OSError:time.sleep(.05)
 else:raise AssertionError('documented server failed')
 for payload,want in payloads[:15]:assert request(payload)==(200,want)
 example={'start':10,'end':20,'samples':[{'device':'d','at':10,'reading':100},{'device':'d','at':15,'reading':30},{'device':'d','at':20,'reading':8}]};assert request(example)==(200,expected(example['samples'],10,20))
 base={'start':0,'end':1,'samples':[{'device':'😀'*40,'at':1,'reading':0}]};assert request(base)[0]==200
 invalid=[]
 for field in ['at','reading']:
  for value in [-1,1000000001,1.0,True,'1',None]:
   p=copy.deepcopy(base);p['samples'][0][field]=value;invalid.append(p)
 p=copy.deepcopy(base);p['samples'][0]['device']='😀'*41;invalid.append(p)
 for p in invalid:assert request(p)[0]==422,p
finally:
 proc.terminate();proc.wait(timeout=5)
print(json.dumps({'random_domain_cases':100,'real_HTTP_random_cases':15,'extra_invalid_cases':len(invalid),'documented_build_install_server_tests':True,'README_example':True,'unicode_boundary':True}))
