"""Real local pair lifecycle; artifact pause is an explicit copied-helper fault."""
import json, os, subprocess, sys, time
from pathlib import Path
from gflo.browser import BrowserStore, RECIPE
from gflo.browser_pair import run
BASE=Path('.gflo/browser-builder-lifecycle').absolute()
if len(sys.argv)>1:
 mode,support=sys.argv[1:]
 def injected(spec,output,**kw):
  if mode!='owner-startup':
   args=spec['browser_args'];i=next(i for i,v in enumerate(args) if ',dst=/journey.cjs,' in v)
   helper=BASE/'paused-helper.cjs';args[i]='type=bind,src='+str(helper)+',dst=/journey.cjs,readonly'
  if mode=='cancel-artifact':
   def cancel():
    ids=subprocess.run(['docker','ps','-q','--filter','name='+spec['browser_name']],capture_output=True,text=True).stdout.split()
    return bool(ids) and subprocess.run(['docker','exec',ids[0],'test','-f','/tmp/in-artifact'],capture_output=True).returncode==0
   kw['cancelled']=cancel
  return run(spec,output,**kw)
 store=BrowserStore(BASE/mode,executor=injected)
 result=store.check({'app':'evaluations/local-browser/app','checks':'evaluations/local-browser/journeys/create-reload','seed':'evaluations/local-browser/journeys/create-reload/seed.json','case':mode,'support':support})
 print(json.dumps({'id':result['id'],'status':result['receipt']['outcome']['status']}))
 raise SystemExit
BASE.mkdir(exist_ok=True)
helper=(RECIPE/'journey.cjs').read_text().replace("clearInterval(timer);runtime.shm", "fs.writeFileSync('/tmp/in-artifact','yes');await sleep(30000);clearInterval(timer);runtime.shm")
(BASE/'paused-helper.cjs').write_text(helper)
rows=[]
for mode in ['owner-startup','owner-artifact','cancel-artifact']:
 store=BrowserStore(BASE/mode);support=store.prepare('.gflo/browser-boundary-prototype')['id']
 owner=subprocess.Popen([sys.executable,__file__,mode,support],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
 seen=False;deadline=time.monotonic()+25
 while time.monotonic()<deadline:
  ids=subprocess.check_output(['docker','ps','-q','--filter','label=gflo.browser='+store.label],text=True).split()
  if mode=='owner-startup' and ids:seen=True;break
  if mode!='owner-startup':
   browser=subprocess.check_output(['docker','ps','-q','--filter','label=gflo.browser='+store.label,'--filter','name=gflo-browser-check-'],text=True).split()
   if browser and subprocess.run(['docker','exec',browser[0],'test','-f','/tmp/in-artifact'],capture_output=True).returncode==0:seen=True;break
  if owner.poll() is not None:break
  time.sleep(.05)
 if mode.startswith('owner-'):owner.kill()
 out,err=owner.communicate(timeout=140)
 deadline=time.monotonic()+30
 while time.monotonic()<deadline:
  remaining=subprocess.check_output(['docker','ps','-aq','--filter','label=gflo.browser='+store.label],text=True).split()
  if not remaining:break
  time.sleep(.1)
 before=[p.name for p in store.root.iterdir()]
 store.cleanup()
 after=[p.name for p in store.root.iterdir()]
 rows.append({'mode':mode,'observed_phase':seen,'exit':owner.returncode,'stdout':out,'stderr':err,'remaining':remaining,'before_cleanup':before,'after_cleanup':after})
 assert seen and not remaining,rows[-1]
Path('.scratch/.sflo/06-autonomy-browser/builder-lifecycle.json').write_text(json.dumps(rows,indent=2)+'\n')
print(json.dumps(rows,indent=2))
