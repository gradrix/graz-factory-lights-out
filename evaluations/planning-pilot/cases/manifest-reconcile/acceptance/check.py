import argparse,copy,json,os,pathlib,subprocess,sys
# Protected oracle failures expose only public criterion scope, never oracle values/source.
def protected_failure(kind, value, tb):
 print('FAIL public requirements A; '+kind.__name__, file=sys.stderr)
sys.excepthook=protected_failure
p=argparse.ArgumentParser();p.add_argument('--project',required=True,type=pathlib.Path);p.add_argument('--phase',choices=['milestone','full'],required=True);a=p.parse_args();project=a.project.resolve();sys.path.insert(0,str(project))
from manifest_tool.domain import compare

def eq(got,want):
 assert type(got)is type(want),(got,want)
 if isinstance(want,dict):assert got.keys()==want.keys();[eq(got[k],v)for k,v in want.items()]
 elif isinstance(want,list):assert len(got)==len(want);[eq(g,v)for g,v in zip(got,want)]
 else:assert got==want,(got,want)
def entry(path,size=1,digest='a'):return {'path':path,'size':size,'sha256':digest*64}
def expect(left,right,added=[],removed=[],modified=[],renamed=[],unchanged=[]):
 before=copy.deepcopy([left,right]);got=compare(left,right);eq(got,{'added':added,'removed':removed,'modified':modified,'renamed':renamed,'unchanged':unchanged});eq([left,right],before)
expect([],[]);expect([entry('keep'),entry('gone',2)],[entry('new',3,'b'),entry('keep')],added=['new'],removed=['gone'],unchanged=['keep'])
expect([entry('a',2)],[entry('a',2,'b')],modified=[{'path':'a','before_size':2,'after_size':2}]);expect([entry('a',2)],[entry('a',3)],modified=[{'path':'a','before_size':2,'after_size':3}])
invalid=[None,{},[entry('/a')],[entry('a//b')],[entry('a/..')],[entry('a\\b')],[entry('a',True)],[entry('a',-1)],[entry('a',1000001)],[entry('a'),entry('a')],[{'path':'a','size':0,'sha256':'A'*64}],[dict(entry('a'),extra=1)],[entry(str(i))for i in range(101)]]
for bad in invalid:
 for left,right in [(bad,[]),([],bad)]:
  original=copy.deepcopy([left,right])
  try:compare(left,right)
  except ValueError:pass
  else:raise AssertionError('Invalid manifest accepted')
  eq([left,right],original)
if a.phase=='full':
 expect([entry('old',5)],[entry('new',5)],renamed=[{'from':'old','to':'new'}]);expect([entry('o2'),entry('o1')],[entry('n')],added=['n'],removed=['o1','o2']);expect([entry('o')],[entry('n2'),entry('n1')],added=['n1','n2'],removed=['o'])
 expect([entry('z'),entry('a',2,'b')],[entry('b',2,'b'),entry('y')],renamed=[{'from':'a','to':'b'},{'from':'z','to':'y'}])
 expect([entry('same'),entry('old',3,'b')],[entry('same',3,'b'),entry('new')],added=['new'],removed=['old'],modified=[{'path':'same','before_size':1,'after_size':3}])
 from manifest_tool.api import run
 payload={'action':'compare','before':[entry('x',5)],'after':[entry('y',5)]};want={'added':[],'removed':[],'modified':[],'renamed':[{'from':'x','to':'y'}],'unchanged':[],'summary':{'before_bytes':5,'after_bytes':5,'delta_bytes':0}};eq(run(payload),want);eq(run({'action':'ping'}),{'ok':True})
 from manifest_tool.report import totals
 eq(totals([entry('x',10)],[entry('y',3)]),{'before_bytes':10,'after_bytes':3,'delta_bytes':-7})
 for value,status,answer in [(json.dumps(payload),0,want),('not json',2,{'error':'invalid input'}),(json.dumps({'action':'compare','before':[],'after':[],'extra':0}),2,{'error':'invalid input'}),('{}',2,{'error':'invalid input'}),(json.dumps({'action':'ping'}),0,{'ok':True})]:
  result=subprocess.run([sys.executable,str(project/'main.py')],input=value,text=True,capture_output=True,cwd='/tmp',timeout=10);assert result.returncode==status and not result.stderr,(result.returncode,result.stderr);eq(json.loads(result.stdout),answer)
 env=dict(os.environ,PYTHONPATH=str(project),PYTHONDONTWRITEBYTECODE='1');code="import unittest,sys;s=unittest.defaultTestLoader.discover(sys.argv[1]);r=unittest.TextTestRunner().run(s);assert r.testsRun>=3 and r.wasSuccessful()";r=subprocess.run([sys.executable,'-c',code,str(project)],cwd='/tmp',env=env,capture_output=True,text=True,timeout=15);assert r.returncode==0,r.stderr
 text=(project/'README.md').read_text();assert len(text.split())>=40 and text!='# Manifest tool\n\nRun `python main.py` with a JSON ping action on standard input.\n'
print('PASS',a.phase)
