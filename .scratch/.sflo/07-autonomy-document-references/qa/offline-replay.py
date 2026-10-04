#!/usr/bin/env python3
"""Post-trial only: actual network-none replay of format3, actual2 and actual1 copies."""
import argparse,hashlib,json,os,pathlib,shutil,subprocess,time,uuid
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def save(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
def hashes(p):
 result={}
 for f in p.rglob('*'):
  assert not f.is_symlink(),'Store link refused'
  if f.is_file() and f!=p/'.lock':result[str(f.relative_to(p))]=sha(f)
 return result
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for name in ['repo','candidate','trial','format2-trial','legacy-trial','output']:p.add_argument('--'+name,type=pathlib.Path,required=True)
 for name in ['candidate-sha256','format2-summary-sha256','legacy-receipt-sha256']:p.add_argument('--'+name,required=True)
 p.add_argument('--run',action='store_true');a=p.parse_args();assert a.run,'Explicit coordinator execution required'
 repo=a.repo.resolve();trial=a.trial.resolve();old=a.format2_trial.resolve();legacy=a.legacy_trial.resolve();out=a.output.resolve();image='sha256:fb1118f126b507965df3c46fdfc52312dfd5262e7b6652ef510bd9298f69a6bc'
 def frozen():
  assert sha(a.candidate)==a.candidate_sha256
  for n,h in read(a.candidate)['files'].items():
   f=(repo/n).resolve();assert f.is_relative_to(repo) and sha(f)==h,n
  assert sha(old/'answers/summary.json')==a.format2_summary_sha256 and sha(legacy/'receipt.json')==a.legacy_receipt_sha256
 frozen();summary=read(trial/'answers/summary.json');assert summary['status']=='complete_pending_independent_semantic_review' and len(summary['rows'])==13 and summary['candidate_sha256']==a.candidate_sha256
 assert sha(trial/'binding.json')==summary['binding_sha256'];assert read(trial/'binding.json')['candidate_sha256']==a.candidate_sha256
 oldsummary=read(old/'answers/summary.json');assert oldsummary['status']=='complete_pending_independent_semantic_review' and len(oldsummary['rows'])==10
 assert oldsummary['candidate_sha256']=='4e1481dede629f9c83be9bbd0002d0975eccbd33820d4456ef5c75bd9eecfc2e'
 assert sum(x['status']=='answer_failure'for x in oldsummary['rows'])==2
 assert not out.exists();out.mkdir(parents=True,mode=0o700)
 originals={'new':trial/'store','format2':old/'store','legacy':legacy/'store'};before={n:hashes(path)for n,path in originals.items()};cases=[]
 for name,path in originals.items():shutil.copytree(path,out/(name+'-store'));assert hashes(out/(name+'-store'))==before[name]
 for group,source,rows,fmt in [('new',trial,summary['rows'],3),('format2',old,oldsummary['rows'],2)]:
  for row in rows:
   assert row.get('id'),'Unpublished operation failure must be assessed before replay'
   case={'group':group,'name':row['name'],'id':row['id'],'format':fmt,'failure':row['status']=='answer_failure'}
   if not case['failure']:case['expected']=read(source/'answers'/row['name']/'answer.json')
   cases.append(case)
 for name,identifier in [('separators','d5d47a808460b75d4c3d170529826af6be3780f21ee98e1bb9d96d4560294870'),('unsupported_future_date','df1c58cca2da34875344007f2d7deaeca2c14dc086fec776e774677b36d861b3')]:
  answer=read(legacy/(name+'-answer.json'));assert answer['id']==identifier;cases.append({'group':'legacy','name':name,'id':identifier,'format':1,'failure':False,'expected':answer})
 assert len(cases)==25;save(out/'cases.json',cases)
 code="""import json,pathlib,sys
sys.path.insert(0,'/source')
from gflo.documents import DocumentStore
rows=[]
for case in json.loads(pathlib.Path('/cases.json').read_text()):
 store=DocumentStore('/'+case['group']+'-store');record=store.resolve(case['id']);assert record['receipt']['format']==case['format'];row={k:case[k]for k in ['group','name','id','format','failure']}
 if case['failure']:
  assert record['receipt']['kind']=='answer_failure'
  try:store.replay(case['id'])
  except ValueError as error:
   assert str(error)=='Replay requires a saved answer ID';row.update(replay_refused=True,error=str(error))
  else:raise AssertionError('Diagnostic replay accepted')
 else:
  actual=store.replay(case['id']);expected=case['expected'];actual.pop('age_seconds',None);expected.pop('age_seconds',None);assert actual==expected,case['name'];row.update(matches_saved=True,answer_status=actual['answer']['status'])
 rows.append(row)
print(json.dumps(rows))
"""
 (out/'child.py').write_text(code);name='gflo-doc-ref-replay-'+uuid.uuid4().hex[:12]
 args=['docker','create','--pull','never','--name',name,'--runtime','runc','--network','none','--read-only','--user',f'{os.getuid()}:{os.getgid()}','--cap-drop','ALL','--security-opt','no-new-privileges','--memory','256m','--memory-swap','256m','--cpus','1','--pids-limit','64','--tmpfs','/tmp:rw,nosuid,nodev,size=16m','--env','PYTHONDONTWRITEBYTECODE=1']
 mounts=[(repo/'gflo','/source/gflo',True),(out/'child.py','/probe.py',True),(out/'cases.json','/cases.json',True)]+[(out/(n+'-store'),'/'+n+'-store',False)for n in originals]
 for source,target,ro in mounts:args+=['--mount',f'type=bind,src={source},dst={target}'+(',readonly'if ro else '')]
 args +=[image,'python','/probe.py'];started=time.monotonic();result=None
 try:
  subprocess.run(args,capture_output=True,text=True,check=True,timeout=15);v=json.loads(subprocess.check_output(['docker','inspect',name],timeout=10))[0]
  assert v['Image']==image and v['HostConfig']['NetworkMode']=='none' and v['HostConfig']['Runtime']=='runc'
  assert {m['Destination']for m in v['Mounts']}=={target for _,target,_ in mounts};save(out/'container.json',{'id':v['Id'],'image':v['Image'],'host':v['HostConfig'],'mounts':v['Mounts'],'config':{k:v['Config'][k]for k in ['User','Cmd','Env']}})
  result=subprocess.run(['docker','start','-a',name],capture_output=True,text=True,timeout=30);(out/'stdout.json').write_text(result.stdout);(out/'stderr.log').write_text(result.stderr);assert result.returncode==0,result.stderr
 finally:
  removal=subprocess.run(['docker','rm','-f',name],capture_output=True,text=True,timeout=30);remaining=subprocess.check_output(['docker','ps','-aq','--filter','name=^/'+name+'$'],text=True,timeout=10).split();save(out/'cleanup.json',{'returncode':removal.returncode,'remaining':remaining});assert not remaining
 assert before=={n:hashes(path)for n,path in originals.items()}=={n:hashes(out/(n+'-store'))for n in originals};frozen()
 save(out/'result.json',{'passed':True,'candidate_sha256':a.candidate_sha256,'trial_summary_sha256':sha(trial/'answers/summary.json'),'format2_summary_sha256':a.format2_summary_sha256,'legacy_receipt_sha256':a.legacy_receipt_sha256,'elapsed_s':time.monotonic()-started,'cases':json.loads(result.stdout),'record_hashes_before':before,'original_and_copy_records_unchanged':True});print('PASS25cross-version replay/diagnostic checks; records unchanged')
if __name__=='__main__':main()
