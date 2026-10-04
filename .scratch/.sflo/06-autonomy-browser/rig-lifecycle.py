#!/usr/bin/env python3
"""Actual owner SIGKILL at startup/artifact; copied helper provides artifact barrier."""
import argparse,hashlib,json,os,pathlib,shutil,subprocess,sys,time

def digest(root):return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file()}
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ['repo','support-store','prior-store','output']:p.add_argument('--'+n,type=pathlib.Path,required=True)
 p.add_argument('--support-id',required=True);p.add_argument('--run',action='store_true');p.add_argument('--child',choices=['owner-startup','owner-artifact']);a=p.parse_args()
 assert a.run;sys.path.insert(0,str(a.repo));from gflo.browser import BrowserStore,RECIPE
 from gflo.browser_pair import run
 if a.child:
  def executor(spec,stream,**kw):
   (a.output/'names.json').write_text(json.dumps({'app':spec['app_name'],'browser':spec['browser_name']}))
   if a.child=='owner-artifact':
    args=spec['browser_args'];i=next(i for i,v in enumerate(args) if ',dst=/journey.cjs,' in v);args[i]='type=bind,src='+str(a.output/'paused-helper.cjs')+',dst=/journey.cjs,readonly'
   return run(spec,stream,**kw)
  store=BrowserStore(a.output/'store',executor=executor)
  fixture=a.repo/'evaluations/local-browser';store.check({'app':str(fixture/'app'),'checks':str(fixture/'journeys/create-reload'),'seed':str(fixture/'journeys/create-reload/seed.json'),'case':a.child,'support':a.support_id});return
 assert not a.output.exists();a.output.mkdir(parents=True);rows=[]
 # Require an actual previously passed result from this qualification, not a fabricated receipt.
 prior=None
 for path in a.prior_store.iterdir():
  if not path.is_dir():continue
  try:
   result=BrowserStore(a.prior_store).inspect(path.name)
   if result['receipt']['kind']=='result' and result['receipt']['outcome']['status']=='passed':prior=path;break
  except (ValueError,KeyError,FileNotFoundError):continue
 assert prior is not None,'No prior actual passed result found'
 for mode in ['owner-startup','owner-artifact']:
  root=a.output/mode;root.mkdir();store=BrowserStore(root/'store');shutil.copytree(a.support_store/a.support_id,store.root/a.support_id);shutil.copytree(prior,store.root/prior.name);before=digest(store.root/prior.name)
  original=(RECIPE/'journey.cjs').read_text();needle='clearInterval(timer);runtime.shm';assert original.count(needle)==1
  (root/'paused-helper.cjs').write_text(original.replace(needle,"require('fs').writeFileSync('/tmp/qa-artifact','1');await new Promise(r=>setTimeout(r,30000));"+needle))
  args=[sys.executable,str(pathlib.Path(__file__).resolve()),'--repo',str(a.repo),'--support-store',str(a.support_store),'--support-id',a.support_id,'--prior-store',str(a.prior_store),'--output',str(root),'--run','--child',mode]
  with (root/'child.log').open('w') as log:
   owner=subprocess.Popen(args,stdout=log,stderr=subprocess.STDOUT);seen=False;deadline=time.monotonic()+35
   try:
    while time.monotonic()<deadline and owner.poll() is None:
     if (root/'names.json').exists():
      names=json.loads((root/'names.json').read_text());target=names['app'] if mode=='owner-startup' else names['browser']
      command=['docker','inspect','--format','{{.State.Running}}',target] if mode=='owner-startup' else ['docker','exec',target,'test','-f','/tmp/qa-artifact']
      result=subprocess.run(command,capture_output=True,text=True,timeout=5)
      if result.returncode==0 and (mode!='owner-startup' or result.stdout.strip()=='true'):seen=True;break
     time.sleep(.05)
   finally:
    owner.kill() if owner.poll() is None else None;owner.wait(timeout=10)
  killed=time.monotonic();deadline=killed+35;remaining=[]
  while time.monotonic()<deadline:
   remaining=subprocess.check_output(['docker','ps','-aq','--filter','label=gflo.browser='+store.label],text=True,timeout=5).split()
   if not remaining:break
   time.sleep(.1)
  candidates=[]
  for path in store.root.iterdir():
   if path.is_dir() and path.name not in [a.support_id,prior.name] and (path/'receipt.json').exists():candidates.append(path.name)
  row={'mode':mode,'observed_phase':seen,'owner_exit':owner.returncode,'remaining':remaining,'removal_s':time.monotonic()-killed,'new_receipts':candidates,'prior_unchanged':before==digest(store.root/prior.name),'fault':'actual SIGKILL; copied helper barrier only for artifact phase'}
  (root/'before-cleanup.json').write_text(json.dumps(row,indent=2));rows.append(row);(a.output/'results.json').write_text(json.dumps(rows,indent=2))
  assert seen and owner.returncode==-9 and not remaining and not candidates and row['prior_unchanged'],row
  store.cleanup();store.inspect(prior.name);assert before==digest(store.root/prior.name)
 print('PASS owner startup/artifact removal and preserved prior result')
if __name__=='__main__':main()
