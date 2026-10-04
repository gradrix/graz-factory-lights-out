"""Actual owner SIGKILL at startup and a copied-helper artifact barrier."""
import json,os,pathlib,subprocess,sys,time
import probe
from gflo.browser_pair import run
b=probe.b;root=probe.PRIVATE/'lifecycle';root.mkdir(exist_ok=True)
os.environ['PYTHONPATH']=str(probe.FROZEN)
def ids(store):return subprocess.check_output(['docker','ps','-aq','--no-trunc','--filter','label=gflo.browser='+store.label],text=True,timeout=15).split()
if len(sys.argv)>1:
 mode,support=sys.argv[1:]
 def execute(spec,output,**kw):
  if mode=='artifact':
   args=spec['browser_args'];index=next(i for i,v in enumerate(args) if ',dst=/journey.cjs,' in v)
   args[index]='type=bind,src='+str(root/'paused.cjs')+',dst=/journey.cjs,readonly'
  return run(spec,output,**kw)
 store=b.BrowserStore(root/mode,executor=execute)
 store.check({'app':str(probe.BASE/'evaluations/local-browser/app'),'checks':str(probe.BASE/'evaluations/local-browser/journeys/create-reload'),'seed':str(probe.BASE/'evaluations/local-browser/journeys/create-reload/seed.json'),'case':mode,'support':support})
 raise SystemExit
helper=(b.RECIPE/'journey.cjs').read_text().replace("clearInterval(timer);runtime.shm", "fs.writeFileSync('/tmp/security-artifact-barrier','ready');await sleep(30000);clearInterval(timer);runtime.shm")
(root/'paused.cjs').write_text(helper)
rows=[]
for mode in ['startup','artifact']:
 store=b.BrowserStore(root/mode);support=store.prepare(probe.BASE/'.gflo/browser-boundary-prototype')['id']
 child=subprocess.Popen([sys.executable,__file__,mode,support],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
 seen=False;until=time.monotonic()+35;observed=[]
 while time.monotonic()<until and child.poll() is None:
  observed=ids(store)
  if mode=='startup' and observed:seen=True;break
  if mode=='artifact':
   for identifier in observed:
    if subprocess.run(['docker','exec',identifier,'test','-f','/tmp/security-artifact-barrier'],capture_output=True,timeout=5).returncode==0:seen=True;break
   if seen:break
  time.sleep(.1)
 child.kill();stdout,stderr=child.communicate(timeout=5);killed=time.monotonic()
 until=time.monotonic()+140
 while time.monotonic()<until:
  remaining=ids(store)
  if not remaining:break
  time.sleep(.1)
 before=[p.name for p in store.root.iterdir()]
 refused=False
 try:store._reserve()
 except ValueError:refused=True
 store.cleanup()
 row={'mode':mode,'phase_observed':seen,'owned_ids_at_kill':observed,'owner_exit':child.returncode,'stdout':stdout,'stderr':stderr,'remaining':remaining,'seconds_to_absence':time.monotonic()-killed,'before_recovery':before,'recovery_required':refused,'after_recovery':[p.name for p in store.root.iterdir()],'support_preserved':store.inspect(support)['id']==support}
 rows.append(row);(probe.OUT/'lifecycle-results.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(row),flush=True)
 assert seen and not remaining and refused and row['support_preserved']
