"""Retained-facts permission controls reproducing v3 B5."""
import json,os,pathlib,tempfile,types
from unittest.mock import patch
import probe
b=probe.b;rows=[]
for mask in [0o002,0o022,0o077]:
 with tempfile.TemporaryDirectory(dir=probe.PRIVATE) as td:
  store,approval,executor=probe.fixture(pathlib.Path(td));work=store.root/'.work-control';work.mkdir()
  old=os.umask(mask)
  try:
   with open(work/'facts.json','x') as stream:json.dump({'cleanup':{'confirmed':False,'uncertain_creates':['owned-app']},'failure':{'kind':'TimeoutExpired','message':'controlled create'}},stream)
  finally:os.umask(old)
  b.write_file(store.root/'.cleanup-required',b.encoded({'run':'owned','names':['owned-app']}))
  mode=oct((work/'facts.json').stat().st_mode&0o777);error=None
  with patch.object(b.subprocess,'run',return_value=types.SimpleNamespace(stdout='')):
   try:store.cleanup(acknowledge_create_uncertainty=True)
   except ValueError as e:error=str(e)
  assert bool(error)==(mask!=0o022)
  rows.append({'umask':oct(mask),'written_mode':mode,'ack_recovery_error':error,'fence_remaining':(store.root/'.cleanup-required').exists()})
(probe.OUT/'mode-results.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(rows,indent=2))
