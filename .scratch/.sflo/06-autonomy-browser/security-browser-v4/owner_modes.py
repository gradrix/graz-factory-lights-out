"""Real frozen pair owner SIGKILL and recovery under two inherited umasks."""
import json,os,pathlib,subprocess,sys,time
import probe
b=probe.b;root=probe.PRIVATE/'owner-modes';root.mkdir(exist_ok=True)
os.environ['PYTHONPATH']=str(probe.FROZEN)
def list_ids(store,running=False):
 args=['docker','ps','-q' if running else '-aq','--no-trunc','--filter','label=gflo.browser='+store.label]
 return subprocess.check_output(args,text=True,timeout=15).split()
def approval(store,support,checks):return {'app':str(probe.BASE/'evaluations/local-browser/app'),'checks':str(checks),'seed':str(probe.BASE/'evaluations/local-browser/journeys/create-reload/seed.json'),'case':'owner-mode','support':support}
if len(sys.argv)>1:
 label,support=sys.argv[1:];store=b.BrowserStore(root/label)
 store.check(approval(store,support,root/'hung'));raise SystemExit
(root/'hung').mkdir(exist_ok=True)
(root/'hung/journey.cjs').write_text("module.exports=async({page,baseURL})=>{await page.goto(baseURL);await page.waitForTimeout(30000)}")
rows=[]
for mask in [0o002,0o077]:
 label=oct(mask);store=b.BrowserStore(root/label);support=store.prepare(probe.BASE/'.gflo/browser-boundary-prototype')['id']
 prior=store.check(approval(store,support,probe.BASE/'evaluations/local-browser/journeys/create-reload'));assert prior['receipt']['outcome']['status']=='passed'
 child=subprocess.Popen([sys.executable,__file__,label,support],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,preexec_fn=lambda:os.umask(mask))
 until=time.monotonic()+30;observed=[]
 while time.monotonic()<until and child.poll() is None:
  observed=list_ids(store,True)
  if len(observed)==2:break
  time.sleep(.1)
 assert len(observed)==2
 child.kill();stdout,stderr=child.communicate(timeout=5);killed=time.monotonic();facts_path=None;facts=None
 until=time.monotonic()+135
 while time.monotonic()<until:
  remaining=list_ids(store)
  for work in store.root.glob('.work-*'):
   candidate=work/'facts.json'
   try:facts=json.loads(candidate.read_bytes());facts_path=candidate
   except (OSError,ValueError):pass
  if not remaining and facts is not None:break
  time.sleep(.1)
 assert not remaining and facts_path is not None
 raw=facts_path.read_bytes();mode=oct(facts_path.stat().st_mode&0o777)
 assert mode=='0o600',mode
 assert facts['cleanup']['confirmed'] is True and not facts['cleanup']['uncertain_creates']
 before=[p.name for p in store.root.iterdir()];store.cleanup()
 assert not (store.root/'.cleanup-required').exists()
 assert store.inspect(prior['id'])['id']==prior['id'] and store.inspect(support)['id']==support
 records=[store.inspect(p.name) for p in store.root.iterdir() if len(p.name)==64]
 recovery=[r for r in records if r['receipt']['kind']=='recovery'];assert len(recovery)==1
 value=recovery[0]['receipt'];key=str(facts_path.relative_to(store.root));kept=value['original_failure_evidence'][key]
 assert kept['sha256']==b.digest(raw) and kept['value']==facts
 assert value['operator_acknowledged_create_uncertainty'] is False
 rows.append({'umask':label,'facts_mode':mode,'owned_running_ids':observed,'owner_exit':child.returncode,'stdout':stdout,'stderr':stderr,'remaining':remaining,'seconds_to_recovered':time.monotonic()-killed,'before_recovery':before,'after_recovery':[p.name for p in store.root.iterdir()],'prior_result_preserved':True,'support_preserved':True,'facts':facts,'recovery':value})
 (probe.OUT/'owner-mode-results.json').write_text(json.dumps(rows,indent=2)+'\n')
 print(json.dumps({'umask':label,'facts_mode':mode,'remaining':remaining,'prior_preserved':True,'recovery_ack':False}),flush=True)
