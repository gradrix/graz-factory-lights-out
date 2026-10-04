"""Independent admission and durable acknowledgment checks; no daemon failure induced."""
import json,pathlib,tempfile,types
from unittest.mock import patch
import probe
b=probe.b;rows=[]
for mode in ['uncertain-create','guardian-exception','missing-guardian-facts','recorded-uncertain-facts','ack-sync-failure','absence-query-failure']:
 with tempfile.TemporaryDirectory(dir=probe.PRIVATE) as td:
  root=pathlib.Path(td);store,approval,executor=probe.fixture(root);prior=store.check(approval)
  def broken(*args,**kw):
   if mode=='guardian-exception':raise OSError('controlled guardian loss')
   value=executor(*args,**kw);value['facts']['cleanup']={'confirmed':False,'uncertain_creates':['owned-app'],'errors':['controlled create response loss']};return value
  store.pair=broken
  try:store.check(approval)
  except (RuntimeError,OSError):pass
  else:raise AssertionError('Uncertain check published')
  if mode in ['missing-guardian-facts','recorded-uncertain-facts']:
   (store.root/'.failure.json').unlink();work=store.root/'.work-owned';work.mkdir()
   if mode=='recorded-uncertain-facts':
    (work/'facts.json').write_text(json.dumps({'cleanup':{'confirmed':False,'uncertain_creates':['owned-browser']},'failure':{'kind':'TimeoutExpired','message':'controlled'}}))
    # Intended-mode control; separate modes.py preserves the actual umask defect.
    (work/'facts.json').chmod(0o644)
  before={str(p.relative_to(store.root)):p.read_bytes() for p in store.root.rglob('*') if p.is_file() and (p.name in ['.failure.json','.cleanup-required','facts.json'])}
  with patch.object(b.subprocess,'run',return_value=types.SimpleNamespace(stdout='')):
   try:store.cleanup()
   except ValueError as e:assert 'Create completion remains uncertain' in str(e)
   else:raise AssertionError('Ordinary cleanup cleared ambiguity')
  assert before=={n:(store.root/n).read_bytes() for n in before}
  try:store.check(approval)
  except ValueError as e:assert 'recovery' in str(e)
  else:raise AssertionError('New admission accepted')
  if mode=='ack-sync-failure':
   with patch.object(b.subprocess,'run',return_value=types.SimpleNamespace(stdout='')),patch.object(b,'sync_directory',side_effect=OSError('controlled recovery commit failure')):
    try:store.cleanup(acknowledge_create_uncertainty=True)
    except OSError:pass
    else:raise AssertionError('Commit fault not exercised')
   assert before=={n:(store.root/n).read_bytes() for n in before}
  if mode=='absence-query-failure':
   with patch.object(b.subprocess,'run',side_effect=OSError('controlled query failure')):
    try:store.cleanup(acknowledge_create_uncertainty=True)
    except OSError:pass
    else:raise AssertionError('Query fault not exercised')
   assert before=={n:(store.root/n).read_bytes() for n in before}
  with patch.object(b.subprocess,'run',return_value=types.SimpleNamespace(stdout='')):store.cleanup(acknowledge_create_uncertainty=True)
  assert not (store.root/'.cleanup-required').exists()
  recovery=[store.inspect(p.name) for p in store.root.iterdir() if len(p.name)==64 and store.inspect(p.name)['receipt']['kind']=='recovery']
  assert len(recovery)==1;value=recovery[0]['receipt']
  assert value['operator_acknowledged_create_uncertainty'] is True
  assert value['daemon_readback']=='currently absent; not proof of create completion'
  for name,raw in before.items():
   kept=value['original_failure_evidence'][name];assert kept['sha256']==b.digest(raw) and kept['value']==json.loads(raw)
  assert store.inspect(prior['id'])['id']==prior['id']
  store.pair=executor;new=store.check(approval);assert new['receipt']['outcome']['status']=='passed'
  rows.append({'mode':mode,'ordinary_recovery_refused':True,'admission_refused':True,'evidence_unchanged_before_ack':True,'prior_preserved':True,'ack_record':value,'admission_after_ack_passed':True})
(probe.OUT/'recovery-results.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps([{'mode':r['mode'],'pass':True} for r in rows],indent=2))
