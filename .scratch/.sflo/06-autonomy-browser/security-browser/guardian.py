"""Deterministic daemon uncertainty injection into the frozen pair guardian."""
import io,json,pathlib,subprocess,tempfile,types
from unittest.mock import patch
import probe
import gflo.browser_pair as pair
rows=[]
for mode in ['clean','create-timeout','absence-query-error','remove-error']:
 with tempfile.TemporaryDirectory(dir=probe.PRIVATE) as td:
  facts=pathlib.Path(td)/'facts.json';calls=[];created=[0]
  spec={'app_name':'owned-app','browser_name':'owned-browser','app_image':'a','browser_image':'b','run':'owned-run','facts':str(facts),'app_args':['docker','run','--rm','--name','owned-app'],'browser_args':['docker','run','--rm','--name','owned-browser','--network','OWNED_APP']}
  def run(args,**kwargs):
   calls.append(args)
   if args[1]=='create':
    if mode=='create-timeout':raise subprocess.TimeoutExpired(args,30)
    created[0]+=1;return types.SimpleNamespace(stdout=(str(created[0])*64).encode())
   if args[1]=='inspect':return types.SimpleNamespace(stdout=json.dumps([{'Id':args[2],'Image':'a' if created[0]==1 else 'b','HostConfig':{},'Config':{},'Mounts':[]}]).encode())
   if args[1]=='rm':return types.SimpleNamespace(returncode=1 if mode in ['remove-error','create-timeout'] else 0,stderr=b'controlled removal failure' if mode=='remove-error' else b'No such container' if mode=='create-timeout' else b'')
   if args[1]=='ps':
    if mode=='absence-query-error':raise subprocess.CalledProcessError(1,args)
    return types.SimpleNamespace(stdout=b'')
   raise AssertionError(args)
  class Attached:
   def __init__(self,args,**kw):self.returncode=0 if args[-1].startswith('2') else None
   def poll(self):return self.returncode
   def kill(self):self.returncode=-9
   def wait(self,**kw):return self.returncode
  stdin=types.SimpleNamespace(buffer=io.BytesIO(json.dumps(spec).encode()+b'\n'))
  with patch.object(pair.sys,'stdin',stdin),patch.object(pair.select,'select',return_value=([],[],[])),patch.object(pair.subprocess,'run',run),patch.object(pair.subprocess,'Popen',Attached):code=pair.main()
  rows.append({'mode':mode,'code':code,'facts':json.loads(facts.read_bytes()),'calls':calls})
(probe.OUT/'guardian-results.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(rows,indent=2))
