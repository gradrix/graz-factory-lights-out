import hashlib
import io
import json
import os
from pathlib import Path
import platform
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from unittest.mock import patch

ROOT=Path(__file__).resolve().parent
CANDIDATE='5295522d04df1e34d2826309e2617ac0a6bf46d7'
REPO=Path(subprocess.check_output(['git','-C',str(ROOT),'rev-parse','--show-toplevel'],text=True).strip())
FROZEN=REPO/'.gflo/security-transport'/CANDIDATE
for relative in ['gflo/__init__.py','gflo/guard.py','gflo/sandbox.py']:
    path=FROZEN/relative;path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes(subprocess.check_output(['git','-C',str(REPO),'show',f'{CANDIDATE}:{relative}']))
sys.path.insert(0,str(FROZEN))
from gflo.guard import run
from gflo.sandbox import Sandbox
# Pin module lookup for each real guardian subprocess as well as this process.
os.chdir(FROZEN)
RESULTS=[]
def record(name,fn):
    try:RESULTS.append({'probe':name,'status':'pass','detail':fn()})
    except Exception as error:RESULTS.append({'probe':name,'status':'fail','error':repr(error)})
def wait_until(fn,seconds=5):
    deadline=time.monotonic()+seconds
    while time.monotonic()<deadline:
        if fn():return
        time.sleep(.025)
    raise AssertionError('controlled process deadline exceeded')
def events(root):
    path=root/'events.jsonl'
    return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []
def args_for(name,code):
    return ['docker','run','--rm','--pull','never','--name',name,'--runtime','runc','--network','none','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges','--memory','128m','--memory-swap','128m','--cpus','1','--pids-limit','16','--shm-size','16m','--user','1234:1234','sha256:'+'a'*64,sys.executable,'-c',code]
def isolated(fn,mode=''):
    with tempfile.TemporaryDirectory(prefix='gflo-transport-security-') as tmp:
        root=Path(tmp)
        fake=root/'bin';fake.mkdir()
        shutil.copy2(ROOT/'fake_docker.py',fake/'docker');(fake/'docker').chmod(0o755)
        env={'PATH':str(fake)+os.pathsep+os.environ['PATH'],'PYTHONPATH':str(FROZEN),'GFLO_SECURITY_FAKE_DOCKER':str(root),'GFLO_SECURITY_FAKE_MODE':mode}
        with patch.dict(os.environ,env):
            try:return fn(root)
            finally:
                # Dispose only known test-owned local executor process groups.
                for row in events(root):
                    if row['event']=='started':
                        try:os.killpg(row['executor'],signal.SIGKILL)
                        except ProcessLookupError:pass

def removed(root,name):
    assert not (root/(name+'.json')).exists()
    assert any(row['event']=='removed' and row['name']==name for row in events(root))
    for row in events(root):
        if row['event']=='started' and row['name']==name:
            process=Path('/proc')/str(row['executor'])/'stat'
            wait_until(lambda:not process.exists() or process.read_text().split(') ',1)[1].startswith('Z '))
def capture(root,code,cap=256,**kwargs):
    output=io.BytesIO();name='security-job'
    result=run(args_for(name,code),name,kwargs.pop('timeout',3),output=output,max_output_bytes=cap,**kwargs)
    removed(root,name)
    return result,output.getvalue()

def binary(root):
    result,data=capture(root,"import sys;sys.stdout.buffer.write(bytes(range(256)));sys.stderr.write('separate diagnostic')",inspect_path=root/'inspect.json')
    assert result['exit_code']==0 and data==bytes(range(256))
    assert result['stdout_bytes']==256
    assert result['output']=='separate diagnostic'
    receipt=json.loads((root/'inspect.json').read_text());source=json.loads((root/'inspection-input.json').read_text())
    assert receipt['image']==source['Image']
    assert receipt['host']==source['HostConfig']
    assert receipt['config']==source['Config']
    assert receipt['mounts']==source['Mounts']
    return {'bytes':len(data),'exit_code':result['exit_code'],'inspection_projection_exact':True,'image':receipt['image']}
record('binary-exact-cap-stderr-separation-inspection',lambda:isolated(binary))

for size in [255,257,65536,1048576]:
    def volume(root,size=size):
        result,data=capture(root,f"import sys;sys.stdout.buffer.write(b'x'*{size})")
        assert len(data)==min(size,256)
        assert result['exit_code']==0 if size<=256 else result['exit_code']!=0
        assert result['limited']==(size>256)
        return {'written_bytes':len(data),'observed_bytes':result['stdout_bytes'],'exit_code':result['exit_code'],'limited':result['limited']}
    record('binary-volume/'+str(size),lambda size=size:isolated(lambda root:volume(root,size)))

def stderr_flood(root):
    result,data=capture(root,"import sys;sys.stderr.buffer.write(b'e'*1048576);sys.stdout.buffer.write(b'ok')")
    assert result['exit_code']==0 and data==b'ok'
    assert len(result['output'])==16384
    return {'diagnostic_retained_bytes':len(result['output']),'artifact_bytes':len(data),'exit_code':result['exit_code']}
record('stderr-million-bytes-retains-bounded-tail',lambda:isolated(stderr_flood))

def text_flood(root):
    name='security-job'
    result=run(args_for(name,"import sys;sys.stdout.buffer.write(b'x'*100000);sys.stderr.write('tail')"),name,3)
    removed(root,name)
    assert result['exit_code']==0 and result['stdout_bytes']==100004
    assert len(result['output'])<16500 and '[truncated' in result['output']
    return {'returned_characters':len(result['output']),'observed_bytes':result['stdout_bytes'],'exit_code':result['exit_code']}
record('sandbox-text-output-retains-bounded-tail',lambda:isolated(text_flood))

for kind in ['timeout','cancel','cancel-exception']:
    def interruption(root,kind=kind):
        name='security-job';output=io.BytesIO()
        def cancel():
            ready=any(row['event']=='started' for row in events(root))
            if ready and kind=='cancel-exception':raise ValueError('controlled callback interruption')
            return ready and kind=='cancel'
        start=time.monotonic()
        try:result=run(args_for(name,'import time;time.sleep(30)'),name,.35 if kind=='timeout' else 3,output=output,cancelled=cancel)
        except ValueError as error:
            assert kind=='cancel-exception' and 'callback' in str(error)
            result={'exit_code':'exception','timed_out':False}
        removed(root,name)
        assert time.monotonic()-start<4
        if kind=='timeout':assert result['exit_code']==124 and result['timed_out']
        if kind=='cancel':assert result['exit_code']==130
        return {'exit_code':result['exit_code'],'removed':True,'elapsed_under_seconds':4}
    record('interruption/'+kind,lambda kind=kind:isolated(lambda root:interruption(root,kind)))

for mode in ['create-fails','inspect-fails','cleanup-fails']:
    def failure(root,mode=mode):
        name='security-job';output=io.BytesIO()
        result=run(args_for(name,"print('completed')"),name,3,output=output,inspect_path=root/'inspect.json')
        assert result['exit_code']!=0
        if mode!='cleanup-fails':removed(root,name)
        else:assert 'cleanup failed' in result['output'].lower()
        if mode in ('create-fails','inspect-fails'):assert not any(row['event']=='started' for row in events(root))
        return {'exit_code':result['exit_code'],'output':result['output'][-300:],'executor_started':any(row['event']=='started' for row in events(root))}
    record('failure/'+mode,lambda mode=mode:isolated(lambda root:failure(root,mode),mode))

def sink_failure(root):
    class Broken:
        def write(self,data):raise OSError('controlled sink failure')
    name='security-job'
    try:run(args_for(name,"print('payload')"),name,3,output=Broken())
    except RuntimeError as error:
        assert 'transport failed' in str(error)
        removed(root,name)
        return {'exception':str(error),'removed':True}
    raise AssertionError('sink failure qualified')
record('binary-sink-write-error-cannot-qualify',lambda:isolated(sink_failure))

def inspect_existing(root):
    target=root/'inspect.json';target.write_text('sentinel')
    result,data=capture(root,"print('never-start')",inspect_path=target)
    assert result['exit_code']!=0 and target.read_text()=='sentinel'
    assert not any(row['event']=='started' for row in events(root))
    return {'exit_code':result['exit_code'],'sentinel_preserved':True,'executor_started':False}
record('existing-inspection-path-preserved-and-no-start',lambda:isolated(inspect_existing))

def owner_kill(root,delayed=False):
    name='security-owner-death'
    pid=os.fork()
    if pid==0:
        try:run(args_for(name,'import time;time.sleep(30)'),name,20,output=io.BytesIO())
        except BaseException:os._exit(81)
        os._exit(82)
    try:
        if delayed:wait_until(lambda:any(row['event']=='command' and row['args'][0]=='create' for row in events(root)))
        else:wait_until(lambda:any(row['event']=='started' for row in events(root)))
        os.kill(pid,signal.SIGKILL)
        _,status=os.waitpid(pid,0);pid=None
        assert os.WIFSIGNALED(status) and os.WTERMSIG(status)==signal.SIGKILL
        wait_until(lambda:any(row['event']=='removed' and row['name']==name for row in events(root)))
        removed(root,name)
        starts=[row for row in events(root) if row['event']=='started']
        if delayed:assert not starts
        return {'owner_signal':'SIGKILL','removed':True,'executor_started':bool(starts),'during_create':delayed}
    finally:
        if pid:
            os.kill(pid,signal.SIGKILL);os.waitpid(pid,0)
record('actual-owner-sigkill-removes-running-test-executor',lambda:isolated(owner_kill))
record('actual-owner-sigkill-during-create-prevents-late-start',lambda:isolated(lambda root:owner_kill(root,True),'create-delayed'))

def sandbox_flags(root):
    sandbox=Sandbox('sha256:'+'a'*64);observed=[]
    sandbox.observe=lambda kind,**fields:observed.append({'kind':kind,**fields})
    result=sandbox.execute(root,[sys.executable,'-c',"print('sandbox-pass')"],acceptance=root,timeout=3)
    assert result['exit_code']==0 and result['output'].strip()=='sandbox-pass'
    create=next(row['args'] for row in events(root) if row['event']=='command' and row['args'][0]=='create')
    for option,value in [('--runtime','runc'),('--network','none'),('--shm-size','16m'),('--pull','never'),('--memory','1g'),('--memory-swap','1g'),('--pids-limit','128'),('--cap-drop','ALL'),('--security-opt','no-new-privileges')]:assert create[create.index(option)+1]==value
    assert '--read-only' in create
    mounts=[create[i+1] for i,x in enumerate(create[:-1]) if x=='--mount']
    assert len(mounts)==2 and all(value.endswith(',readonly') for value in mounts)
    assert [row['kind'] for row in observed]==['container_running','container_finished']
    assert observed[-1]['exit_code']==0
    return {'command_flags_checked':True,'readonly_mounts':2,'events':[row['kind'] for row in observed]}
record('sandbox-refactor-preserves-constraints-and-observation',lambda:isolated(sandbox_flags))

def cleanup_failure_during_timeout(root):
    name='security-job';output=io.BytesIO()
    result=run(args_for(name,'import time;time.sleep(30)'),name,.4,output=output)
    assert result['exit_code']!=0 and 'cleanup failed' in result['output'].lower()
    assert any(row['event']=='cleanup-failed' for row in events(root))
    assert (root/(name+'.json')).exists()
    return {'exit_code':result['exit_code'],'timed_out':result['timed_out'],'explicit_cleanup_diagnostic':True,'fake_executor_cleanup_not_claimed':True}
record('cleanup-failure-during-timeout-cannot-qualify',lambda:isolated(cleanup_failure_during_timeout,'cleanup-fails'))

result={'candidate':CANDIDATE,'python':platform.python_version(),'source_sha256':{name:hashlib.sha256((FROZEN/'gflo'/name).read_bytes()).hexdigest() for name in ['guard.py','sandbox.py']},'execution':'test-owned fake docker CLI and local child executors; no Docker daemon or containers','pass':sum(row['status']=='pass' for row in RESULTS),'fail':sum(row['status']=='fail' for row in RESULTS),'results':RESULTS}
(FROZEN/'rerun-results.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({key:value for key,value in result.items() if key!='results'},indent=2))
for row in RESULTS:
    if row['status']=='fail':print(json.dumps(row))
print(f'Rerun evidence: {FROZEN / "rerun-results.json"}')
sys.exit(1 if result['fail'] else 0)
