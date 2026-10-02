import sys, os, json, time, subprocess, tempfile, threading, urllib.request, urllib.error
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))
from gflo.runner import Factory
from gflo.observe import Observer
from gflo.sandbox import Sandbox
from gflo.web import server

def wait(pred, label, timeout=20):
    end=time.monotonic()+timeout
    while time.monotonic()<end:
        if pred(): return
        time.sleep(.1)
    raise AssertionError(label)

def get(url, method='GET', headers=None):
    try:
        with urllib.request.urlopen(urllib.request.Request(url,method=method,headers=headers or {})) as r: return r.status,r.read()
    except urllib.error.HTTPError as e: return e.code,e.read()

with tempfile.TemporaryDirectory(prefix='gflo-independent-qa-') as tmp:
    root=Path(tmp); repo=root/'repo'; repo.mkdir(); (repo/'app.py').write_text('value=1\n')
    for args in (['init','-q'],['add','.'],['-c','user.name=QA','-c','user.email=qa@local','commit','-qm','base']): subprocess.run(['git','-C',str(repo),*args],check=True)
    accept=root/'accept'; accept.mkdir(); (accept/'check.py').write_text('from pathlib import Path\nassert Path("app.py").read_text()=="value=1\\n"\n')
    task=root/'task.json'; task.write_text(json.dumps(dict(repo=str(repo),acceptance=str(accept),objective='Preserve working app',checks=[['python','-I','/acceptance/check.py']],max_attempts=2)))
    box=Sandbox(); f=Factory(root/'state',lambda *a: {},box.verify,box.cleanup); obs=Observer(f.state)
    http=server(f.state,0); threading.Thread(target=http.serve_forever,daemon=True).start(); base=f'http://127.0.0.1:{http.server_port}'
    code='''import sys\nfrom gflo.runner import Factory\nfrom gflo.sandbox import Sandbox\nb=Sandbox()\ndef work(w,*a):\n return b.execute(w,['python','-c',"import time; from pathlib import Path; p=Path('writer'); [(p.write_text(str(n)),time.sleep(.1)) for n in range(1000)]"],timeout=100)\nf=Factory(sys.argv[1],work,b.verify,b.cleanup)\nf.resume(sys.argv[2])\n'''
    ids=[]
    for mode in ('kill','cancel'):
        run=f.create(task); ids.append(run); cursor=obs.events(run)[-1]['seq']; ws=f.state/run/'workspace'; writer=ws/'writer'
        with open(root/(mode+'.log'),'w') as log:
            proc=subprocess.Popen([sys.executable,'-c',code,str(f.state),run],stdout=log,stderr=log)
            try:
                wait(lambda: writer.exists(),'container writer did not start')
                assert obs.status(run)['owner_alive']
                if mode=='kill': proc.kill()
                else: f.cancel(run)
                proc.wait(timeout=50)
                wait(lambda: not subprocess.check_output(['docker','ps','-q','--filter','label=gflo.workspace='+__import__('hashlib').sha256(str(ws.resolve()).encode()).hexdigest()]).strip(),'orphan writer remained')
                snap=writer.read_text(); time.sleep(.4); assert writer.read_text()==snap
                status=json.loads(get(base+'/api/runs/'+run)[1]); assert status['status']==('interrupted' if mode=='kill' else 'cancelled'),status
                assert not status['owner_alive']
                assert f.resume(run)['status']=='accepted'; assert obs.status(run)['attempts']==2
                assert sum(e['kind']=='accepted' for e in obs.events(run))==1
                before=obs.events(run); f.resume(run); assert obs.events(run)==before
                fresh=json.loads(get(base+'/api/runs/'+run+'/events?after='+str(cursor))[1]); assert fresh and all(e['seq']>cursor for e in fresh)
                print(mode,'real Docker writer stopped; honest death; resumed at attempt 2; accepted once; cursor reconnect PASS',flush=True)
            finally:
                if proc.poll() is None: proc.kill();proc.wait()
                box.cleanup(ws)
    run=f.create(task); ids.append(run); f.resume(run)
    assert set(r['id'] for r in json.loads(get(base+'/api/runs')[1]))==set(ids)
    print('external HTTP client sees all three accepted runs PASS',flush=True)
    for method in ('POST','PUT','PATCH','DELETE'):
        assert get(base+'/api/runs/'+run,method)[0]==501
    assert get(base,headers={'Host':'evil.example'})[0]==403
    for name in ('../task.json','task.json','snapshot.git/config','/etc/passwd','attempts/1/input.json'):
        assert get(base+'/api/runs/'+run+'/artifact?name='+urllib.parse.quote(name))[0]==404
    artifact=f.state/run/'attempts/1/worker.json'; artifact.write_text('password=hidden api_key="hidden" Authorization: Bearer hidden\n'+'x'*1100000)
    body=get(base+'/api/runs/'+run+'/artifact?name=attempts/1/worker.json')[1]
    assert b'hidden' not in body and body.endswith(b'[truncated at 1 MiB]') and len(body)<1048700
    artifact.unlink();artifact.symlink_to(task);assert get(base+'/api/runs/'+run+'/artifact?name=attempts/1/worker.json')[0]==404
    print('HTTP writes/host/path/private artifacts/symlinks rejected; secret redaction and 1MiB bound PASS',flush=True)
    (f.state/run/'workspace/app.py').write_text('changed')
    assert json.loads(get(base+'/api/runs/'+run)[1])['status']=='invalidated'
    print('accepted workspace tampering invalidates HTTP status PASS',flush=True)
    http.shutdown();http.server_close()
