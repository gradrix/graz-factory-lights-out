import sys,os
from pathlib import Path
sys.path[:0]=['/tmp/gflo-review-candidate1','/tmp/gflo-review-candidate1/tests']
from test_runner import RunnerTests
from gflo.runner import Factory

def run(crash):
 t=RunnerTests(); t.setUp(); f=Factory(t.root/'state',lambda *a:{},lambda *a:{'passed':True}); rid=f.create(t.task)
 if crash:
  pid=os.fork()
  if pid==0:
   original=Path.mkdir
   def mkdir(path,*args,**kwargs):
    result=original(path,*args,**kwargs)
    if path.name=='1' and path.parent.name=='attempts': os._exit(77)
    return result
   Path.mkdir=mkdir
   f.resume(rid); os._exit(0)
  _,status=os.waitpid(pid,0); assert os.waitstatus_to_exitcode(status)==77
 try:
  result=Factory(t.root/'state',lambda *a:{},lambda *a:{'passed':True}).resume(rid)
  assert result['status']=='accepted'
  print('RECOVERY_ASSERTION_PASS',crash)
 except FileExistsError as e:
  assert crash
  print('RECOVERY_ASSERTION_FAIL',crash,str(e))
 finally:t.doCleanups()
run(False);run(True)
