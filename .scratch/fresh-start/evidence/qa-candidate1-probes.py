import sys,json,hashlib,os
from pathlib import Path
sys.path[:0]=['/tmp/gflo-review-candidate1','/tmp/gflo-review-candidate1/tests']
from test_runner import RunnerTests
from gflo.runner import Factory
from gflo.sandbox import Sandbox

def fixture():
 t=RunnerTests(); t.setUp(); return t

def crash_directory():
 t=fixture(); f=Factory(t.root/'state',lambda *a:{},lambda *a:{'passed':True}); rid=f.create(t.task)
 # Exact durable state of SIGKILL after attempt.mkdir and before DB transaction.
 (f.state/rid/'attempts/1').mkdir(parents=True)
 try: f.resume(rid); result='recovered'
 except Exception as e: result=f'{type(e).__name__}: {e}'
 print('CRASH_BEFORE_DB',result)
 t.doCleanups()
def accepted_integrity(tamper):
 t=fixture(); f=Factory(t.root/'state',lambda *a:{},lambda *a:{'passed':True}); rid=f.create(t.task); r=f.resume(rid)
 if tamper: (Path(r['workspace'])/'app.py').write_text('broken\n')
 print('ACCEPTED_INTEGRITY',tamper,f.resume(rid)['status'])
 t.doCleanups()
def sandbox():
 t=fixture(); s=Sandbox(); code="""import os,socket,pathlib
assert not pathlib.Path('/var/run/docker.sock').exists()
assert not pathlib.Path('/acceptance').exists()
assert os.environ.get('GFLO_QA_SECRET') is None
try: socket.create_connection(('1.1.1.1',443),timeout=1)
except OSError: pass
else: raise AssertionError('network available')
try: pathlib.Path('/etc/qa-probe').write_text('x')
except OSError: pass
else: raise AssertionError('root writable')
print('BOUNDARIES_OK')
"""
 os.environ['GFLO_QA_SECRET']='must-not-leak'
 print('SANDBOX',s.execute(t.repo,['python','-c',code]))
 t.doCleanups()
manifest=json.loads(Path('/home/gradrix/repos/gflo/.scratch/fresh-start/evidence/candidate1.json').read_text())
assert all(hashlib.sha256((Path(manifest['root'])/p).read_bytes()).hexdigest()==v for p,v in manifest['files'].items())
print('MANIFEST_OK',manifest['identity'])
accepted_integrity(False); accepted_integrity(True); crash_directory(); sandbox()
