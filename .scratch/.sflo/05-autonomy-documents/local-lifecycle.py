"""Controlled stalled-fetch injection; real document Docker envelope and guardian."""
import json, os, subprocess, sys, time
from pathlib import Path
from gflo import guard
from gflo.documents import DocumentStore
BASE=Path('.gflo/document-lifecycle-builder').absolute()
APP=json.loads(Path('.scratch/.sflo/05-autonomy-documents/first-approval.json').read_text())
if len(sys.argv)>1:
    mode=sys.argv[1]
    def stalled(args,*rest,**kwargs):
        args=args[:-4]+['python','-c','import time; time.sleep(60)']
        return guard.run(args,*rest,**kwargs)
    store=DocumentStore(BASE/mode,executor=stalled)
    start=time.monotonic()
    try:store.acquire(APP,cancelled=lambda:mode=='cancel' and time.monotonic()-start>2)
    except ValueError as error:print(str(error),flush=True)
    raise SystemExit
results={}
for mode in ['cancel','owner-death']:
    process=subprocess.Popen([sys.executable,__file__,mode],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    store=DocumentStore(BASE/mode)
    deadline=time.monotonic()+20;seen=False
    while time.monotonic()<deadline:
        ids=subprocess.check_output(['docker','ps','-aq','--filter','label=gflo.documents='+store.label],text=True).split()
        if ids:seen=True;break
        time.sleep(.05)
    if mode=='owner-death':process.kill()
    out,err=process.communicate(timeout=120)
    deadline=time.monotonic()+20
    while time.monotonic()<deadline:
        ids=subprocess.check_output(['docker','ps','-aq','--filter','label=gflo.documents='+store.label],text=True).split()
        if not ids:break
        time.sleep(.1)
    reusable=[p.name for p in store.root.iterdir() if len(p.name)==64]
    before=[p.name for p in store.root.iterdir()]
    store.cleanup()
    results[mode]={'observed_container':seen,'remaining_containers':ids,'reusable_records':reusable,'before_cleanup':before,'after_cleanup':[p.name for p in store.root.iterdir()],'exit':process.returncode,'stdout':out,'stderr':err}
    assert seen and not ids and not reusable,results[mode]
Path('.scratch/.sflo/05-autonomy-documents/builder-local-lifecycle.json').write_text(json.dumps(results,indent=2)+'\n')
