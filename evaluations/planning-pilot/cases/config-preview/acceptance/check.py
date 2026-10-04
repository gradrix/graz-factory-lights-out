import argparse,copy,json,os,pathlib,shutil,socket,subprocess,sys,tempfile,time,tomllib,urllib.request,urllib.error,zipfile
# Protected oracle failures expose only public criterion scope, never oracle values/source.
def protected_failure(kind, value, tb):
 print('FAIL public requirements B; '+kind.__name__, file=sys.stderr)
sys.excepthook=protected_failure
p=argparse.ArgumentParser();p.add_argument('--project',required=True,type=pathlib.Path);p.add_argument('--phase',choices=['milestone','full'],required=True);a=p.parse_args();project=a.project.resolve()
assert tomllib.loads((project/'pyproject.toml').read_text())['project']['dependencies']==['fastapi==0.115.12','uvicorn==0.34.2']
assert tomllib.loads((project/'pyproject.toml').read_text())['build-system']=={'requires':['setuptools==78.1.0'],'build-backend':'setuptools.build_meta'}
scratch=tempfile.TemporaryDirectory();work=pathlib.Path(scratch.name);shutil.copytree(project,work/'build');(work/'wheels').mkdir();site=work/'site';site.mkdir();env=dict(os.environ,PYTHONPATH='/opt/deps',PYTHONDONTWRITEBYTECODE='1')
proc=subprocess.run([sys.executable,'-c','import setuptools.build_meta as b;b.build_wheel("'+str(work/'wheels')+'")'],cwd=work/'build',env=env,capture_output=True,text=True,timeout=30);assert proc.returncode==0,proc.stderr
wheels=list((work/'wheels').glob('*.whl'));assert len(wheels)==1
with zipfile.ZipFile(wheels[0])as z:
 for name in z.namelist():assert not name.startswith('/') and '..'not in pathlib.PurePosixPath(name).parts
 z.extractall(site)
sys.path[:0]=[str(site),'/opt/deps'];env['PYTHONPATH']=str(site)+':/opt/deps'
from config_preview.domain import preview
from config_preview.errors import Conflict

def eq(g,w):
 assert type(g)is type(w),(g,w)
 if isinstance(w,dict):assert g.keys()==w.keys();[eq(g[k],v)for k,v in w.items()]
 elif isinstance(w,(list,tuple)):assert len(g)==len(w);[eq(x,y)for x,y in zip(g,w)]
 else:assert g==w,(g,w)
def op(kind,path,value=None):return dict(op=kind,path=path,**({}if kind=='remove'else {'value':value}))
def audit(i,kind,path,bp,bv,ap,av):return {'index':i,'op':kind,'path':path,'before':{'present':bp,'value':bv},'after':{'present':ap,'value':av}}
def good(base,ops,want):
 old=copy.deepcopy([base,ops]);result=preview(base,ops);eq(result,want);eq([base,ops],old);result['document']['qaAliasProbe']=1
 for child in result['document'].values():
  if isinstance(child,dict):child['qaNestedAliasProbe']=2
 eq([base,ops],old)
from config_preview.audit import event
x={'a':1};path=['x'];ev=event(0,'set',path,False,99,True,x);eq(ev,audit(0,'set',['x'],False,None,True,{'a':1}));x['a']=2;path.append('changed');eq(ev,audit(0,'set',['x'],False,None,True,{'a':1}))
eq(preview({},[]),{'document':{},'audit':[]})
good({'a':None},[op('set',['a'],3),op('set',['nested'],{'x':True}),op('remove',['a'])],{'document':{'nested':{'x':True}},'audit':[audit(0,'set',['a'],True,None,True,3),audit(1,'set',['nested'],False,None,True,{'x':True}),audit(2,'remove',['a'],True,3,False,None)]})
good({'a':{'x':1}},[op('set',['a','x'],2)],{'document':{'a':{'x':2}},'audit':[audit(0,'set',['a','x'],True,1,True,2)]})
invalid=[([],[]),({'a':1.0},[]),({'a':[]},[]),({'a':1000001},[]),({'bad key':0},[]),({},[op('set',[],0)]),({},[op('set',['a'],[]) ]),({},[dict(op('set',['a'],0),extra=1)]),({},[{'op':'remove','path':['a'],'value':1}]),({},[op('set',['a'],'x'*81)]),({},[op('remove',['x']),{'op':'invalid','path':['a']}]),({},[op('set',['a'],0)]*51)]
for base,ops in invalid:
 old=copy.deepcopy([base,ops])
 try:preview(base,ops)
 except Conflict:raise AssertionError('Shape error must precede conflict')
 except ValueError:pass
 else:raise AssertionError('Invalid shape accepted')
 eq([base,ops],old)
if a.phase=='full':
 cases=[({},[op('set',['x'],1),op('remove',['no'])],1,'missing'),({},[op('set',['no','x'],1)],0,'parent_missing'),({'a':None},[op('set',['a','x'],1)],0,'parent_not_object'),({'a':False},[op('test',['a'],0)],0,'test_failed'),({},[op('test',['a'],None)],0,'test_failed')]
 for base,ops,index,code in cases:
  old=copy.deepcopy([base,ops])
  try:preview(base,ops)
  except Conflict as error:eq(error.index,index);eq(error.code,code)
  else:raise AssertionError('Conflict accepted')
  eq([base,ops],old)
 good({'a':{'x':1,'y':None}},[op('test',['a'],{'y':None,'x':1})],{'document':{'a':{'x':1,'y':None}},'audit':[audit(0,'test',['a'],True,{'x':1,'y':None},True,{'x':1,'y':None})]})
 base={f'k{i}':0 for i in range(199)}
 try:preview(base,[op('set',['new'],1)])
 except Conflict as e:eq(e.index,0);eq(e.code,'limit')
 else:raise AssertionError('Capacity accepted')
 # Actual installed package, actual loopback HTTP; no external network.
 sock=socket.socket();sock.bind(('127.0.0.1',0));port=sock.getsockname()[1];sock.close();server=subprocess.Popen([sys.executable,'-m','uvicorn','config_preview.app:app','--host','127.0.0.1','--port',str(port),'--log-level','error'],cwd='/tmp',env=env,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
 def http(path,payload=None):
  request=urllib.request.Request('http://127.0.0.1:'+str(port)+path,data=None if payload is None else json.dumps(payload).encode(),headers={'Content-Type':'application/json'})
  try:
   with urllib.request.urlopen(request,timeout=3)as r:return r.status,json.load(r)
  except urllib.error.HTTPError as r:return r.code,json.load(r)
 try:
  deadline=time.monotonic()+8
  while True:
   try:status,value=http('/health');break
   except OSError:
    if time.monotonic()>deadline:raise
    time.sleep(.05)
  eq(status,200);eq(value,{'status':'ok'});eq(http('/sum',{'values':[1,-3,2]}),(200,{'total':0}));assert http('/sum',{'values':[True]})[0]==422;assert http('/missing')[0]==404
  request={'base':{'a':None},'operations':[op('remove',['a'])]};eq(http('/config/preview',request),(200,{'document':{},'audit':[audit(0,'remove',['a'],True,None,False,None)]}))
  for base,ops,index,code in cases:eq(http('/config/preview',{'base':base,'operations':ops}),(409,{'error':{'index':index,'code':code}}))
  for base,ops in invalid:assert http('/config/preview',{'base':base,'operations':ops})[0]==422
  assert http('/config/preview',dict(request,extra=1))[0]==422
  eq(http('/config/preview',{'base':{},'operations':[]}),(200,{'document':{},'audit':[]}))
 finally:
  server.terminate();server.wait(timeout=5)
 code="import unittest,sys;s=unittest.defaultTestLoader.discover(sys.argv[1]);r=unittest.TextTestRunner().run(s);assert r.testsRun>=3 and r.wasSuccessful()";r=subprocess.run([sys.executable,'-c',code,str(project)],cwd='/tmp',env=env,capture_output=True,text=True,timeout=15);assert r.returncode==0,r.stderr
 assert len((project/'README.md').read_text().split())>=40
print('PASS',a.phase)
