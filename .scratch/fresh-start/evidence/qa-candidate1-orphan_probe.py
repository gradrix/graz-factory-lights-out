import sys,tempfile,os,time,signal,multiprocessing
from pathlib import Path
sys.path.insert(0,'/tmp/gflo-review-candidate1')
from gflo.sandbox import Sandbox
with tempfile.TemporaryDirectory() as d:
 w=Path(d)
 def launch(): Sandbox().execute(w,['sh','-c','while true; do date +%s%N > tick; sleep 0.1; done'])
 p=multiprocessing.Process(target=launch);p.start()
 for _ in range(100):
  if (w/'tick').exists():break
  time.sleep(.05)
 assert (w/'tick').exists()
 os.kill(p.pid,signal.SIGKILL);p.join()
 a=(w/'tick').read_text();time.sleep(.3);b=(w/'tick').read_text()
 assert a!=b
 print('ORPHAN_WRITER_SURVIVES_CONTROLLER_DEATH')
 Sandbox().cleanup(w)
 a=(w/'tick').read_text();time.sleep(.3);assert a==(w/'tick').read_text()
 print('CLEANUP_STOPS_WRITER')
