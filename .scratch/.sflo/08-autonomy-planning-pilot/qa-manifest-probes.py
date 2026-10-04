#!/usr/bin/env python3
"""Run INSIDE pinned offline container; candidate read-only at /candidate, no /workspace.
Stdlib only. Records observed documentation defects without modifying candidate.
Usage: python /probe/qa-manifest-probes.py --arm 1|2
"""
import argparse,copy,importlib,json,pathlib,re,subprocess,sys

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--arm',type=int,choices=[1,2],required=True);args=parser.parse_args()
 root=pathlib.Path('/candidate');assert root.is_dir()and not pathlib.Path('/workspace').exists()
 assert sys.version_info[:3]==(3,12,13);sys.dont_write_bytecode=True;sys.path.insert(0,str(root))
 from manifest_tool.domain import compare
 from manifest_tool.api import run
 rows=[]
 def check(name,call):
  try:call();rows.append({'name':name,'passed':True})
  except Exception as error:rows.append({'name':name,'passed':False,'error':repr(error)})
 def equal(a,b):assert type(a)is type(b)and a==b,(a,b)
 def entry(path,size=1,digest='a'*64):return {'path':path,'size':size,'sha256':digest}
 def boundaries():
  before=[entry('p'+str(i),1000000)for i in range(99)]+[entry('x'*120,0)];old=copy.deepcopy(before)
  result=run({'action':'compare','before':before,'after':before});equal(len(result['unchanged']),100);equal(result['summary']['before_bytes'],99000000);equal(before,old)
  for bad in [entry('x'*121),entry('x\n'),entry('é'),entry('x',digest='a'*63+'\n'),entry('x',True),entry('x',1.0)]:
   sample=[entry('ok'),bad];snapshot=copy.deepcopy(sample)
   for left,right in [(sample,[]),([],sample)]:
    try:compare(left,right)
    except ValueError:pass
    else:raise AssertionError('Invalid boundary accepted')
   equal(sample,snapshot)
  try:compare([entry('n'+str(i))for i in range(101)],[])
  except ValueError:pass
  else:raise AssertionError('101 entries accepted')
 def ambiguity():
  for old,new in [(['o1','o2'],['n1']),(['o1'],['n1','n2'])]:
   before=[entry(x)for x in old]+[entry('soloOld',2)];after=[entry(x)for x in new]+[entry('soloNew',2)]
   saved=copy.deepcopy([before,after]);expected={'added':new,'removed':old,'modified':[],'renamed':[{'from':'soloOld','to':'soloNew'}],'unchanged':[]}
   equal(compare(before,after),expected);equal(compare(before[::-1],after[::-1]),expected);equal([before,after],saved)
 def cli():
  for text,code,want in [(' {"action":"ping"}',0,{'ok':True}),('not json',2,{'error':'invalid input'})]:
   result=subprocess.run([sys.executable,str(root/'main.py')],input=text,text=True,capture_output=True,cwd='/tmp',timeout=10);equal(result.returncode,code);equal(json.loads(result.stdout),want);equal(result.stderr,'')
 check('public-boundaries-and-nonmutation',boundaries);check('asymmetric-renames-permutation',ambiguity);check('absolute-cli-unrelated-cwd',cli)
 # Arm1 exact advertised root command. Arm2 original A6 project-root command
 # with actual path; literal README /workspace command recorded separately.
 command=[sys.executable,'-m','unittest','discover','-s','.']
 tests=subprocess.run(command,cwd=root,text=True,capture_output=True,timeout=30)
 rows.append({'name':'documented-root-unittest'if args.arm==1 else 'A6-relocated-root-unittest','command':command,'cwd':str(root),'exit':tests.returncode,'stdout':tests.stdout,'stderr':tests.stderr,'passed':tests.returncode==0})
 readme=(root/'README.md').read_text()
 if args.arm==1:
  match=re.search(r"echo '(\{\"action\":\"compare\".*?\})' \| python main.py",readme);assert match
  payload=match.group(1);expected=json.loads(re.search(r'```json\n(.*?)\n```',readme,re.S).group(1))
 else:
  match=re.search(r"<<'JSON'\n(.*?)\nJSON\n(\{[^\n]+\})",readme,re.S);assert match
  payload=match.group(1);expected=json.loads(match.group(2))
 result=subprocess.run([sys.executable,str(root/'main.py')],input=payload,text=True,capture_output=True,cwd=root,timeout=10)
 try:actual=json.loads(result.stdout)
 except ValueError:actual=None
 rows.append({'name':'literal-readme-compare-payload-and-outcome','path_substitution_only':args.arm==2,'expected_exit':0,'expected':expected,'exit':result.returncode,'actual':actual,'stderr':result.stderr,'digest_lengths':[len(e['sha256'])for side in ['before','after']for e in json.loads(payload)[side]],'passed':result.returncode==0 and actual==expected and result.stderr==''})
 print(json.dumps({'arm':args.arm,'python':sys.version,'candidate_mount':str(root),'workspace_absent':True,'rows':rows},indent=2))
 # Honest failing status for any required behavior/documentation mismatch.
 return 0 if all(row['passed']for row in rows)else 1
if __name__=='__main__':raise SystemExit(main())
