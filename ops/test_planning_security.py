"""Independent prototype boundaries; local Git/files/processes, no model or Docker."""
import copy
from contextlib import contextmanager, ExitStack
import hashlib
import json
import os
from pathlib import Path
import stat
import signal
import subprocess
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parent))
import planning_pilot_prototype as p

class SecurityControls(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
 def source(self,name='source'):
  root=self.root/name;root.mkdir();(root/'data.txt').write_text('fixed\n');return root
 def plain(self,repo,*args,env=None):
  return subprocess.run(['git','-C',str(repo),*args],check=True,capture_output=True,env=env,timeout=5)
 def test_clean_git_blocks_inherited_hook_filter_environment(self):
  home=self.root/'home';home.mkdir();hooks=self.root/'hooks';hooks.mkdir();hit=self.root/'hook-hit';filtered=self.root/'filter-hit'
  hook=hooks/'pre-commit';hook.write_text('#!/bin/sh\ntouch '+str(hit)+'\n');hook.chmod(0o700)
  attrs=self.root/'attrs';attrs.write_text('* filter=owned\n')
  config=self.root/'config';config.write_text('[core]\n hooksPath = '+str(hooks)+'\n attributesFile = '+str(attrs)+'\n[filter "owned"]\n clean = touch '+str(filtered)+'; cat\n required = true\n')
  # Positive control must not inherit another test's sanitized Git overrides.
  env={k:v for k,v in os.environ.items() if not k.startswith('GIT_')}
  env.update(HOME=str(home),GIT_CONFIG_GLOBAL=str(config),GIT_CONFIG_NOSYSTEM='1')
  control=self.source('positive');self.plain(control,'init','-q',env=env);self.plain(control,'add','--all',env=env)
  self.plain(control,'-c','user.name=Owned','-c','user.email=owned@local','commit','-qm','control',env=env)
  self.assertTrue(hit.exists());self.assertTrue(filtered.exists());hit.unlink();filtered.unlink()
  source=self.source();env.update(GIT_CONFIG_COUNT='1',GIT_CONFIG_KEY_0='core.hooksPath',GIT_CONFIG_VALUE_0=str(hooks),GIT_DIR=str(control/'.git'),GIT_WORK_TREE=str(control))
  with patch.dict(os.environ,env,clear=True):p.initialize_repository(source,self.root/'safe')
  self.assertFalse(hit.exists());self.assertFalse(filtered.exists());self.assertEqual((self.root/'safe/data.txt').read_bytes(),b'fixed\n')
 def test_git_template_hook_disabled_with_positive_control(self):
  template=self.root/'template';(template/'hooks').mkdir(parents=True);hit=self.root/'template-hit'
  hook=template/'hooks/pre-commit';hook.write_text('#!/bin/sh\ntouch '+str(hit)+'\n');hook.chmod(0o700)
  env={k:v for k,v in os.environ.items() if not k.startswith('GIT_')};env.update(GIT_TEMPLATE_DIR=str(template),GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL='/dev/null')
  control=self.source('positive');self.plain(control,'init','-q',env=env);self.plain(control,'add','--all',env=env);self.plain(control,'-c','user.name=Owned','-c','user.email=owned@local','commit','-qm','control',env=env)
  self.assertTrue(hit.exists());hit.unlink()
  with patch.dict(os.environ,env,clear=True):p.initialize_repository(self.source(),self.root/'safe')
  self.assertFalse(hit.exists())
 def test_reserved_control_files_refuse_before_git(self):
  for index,name in enumerate(['.git/config','.git/hooks/pre-commit','sub/.git/config','.git','.gitattributes','.gitmodules','.gitignore','sub/.GiTaTtRiBuTeS']):
   with self.subTest(name=name):
    source=self.source('source'+str(index));target=source/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_text('* export-ignore\n')
    with patch.object(p,'git') as git:
     with self.assertRaises(ValueError):p.initialize_repository(source,self.root/('dest'+str(index)))
     git.assert_not_called()
 def test_checked_types_and_special_modes(self):
  source=self.source();target=source/'bad';outside=self.root/'outside';outside.write_text('untouched')
  for kind in ['symlink','hardlink','fifo','setuid','setgid-dir']:
   with self.subTest(kind=kind):
    if kind=='symlink':target.symlink_to(outside)
    elif kind=='hardlink':os.link(outside,target)
    elif kind=='fifo':os.mkfifo(target)
    elif kind=='setuid':target.write_text('x');target.chmod(0o4755)
    else:target.mkdir();target.chmod(0o2755)
    with self.assertRaises(ValueError):p.checked_tree(source)
    if target.is_dir():target.rmdir()
    else:target.unlink()
  self.assertEqual(outside.read_text(),'untouched')
 def test_checked_exact_capacity_and_copy(self):
  source=self.source();(source/'data.txt').write_bytes(b'x'*200000);(source/'data.txt').chmod(0o640)
  destination=self.root/'dest';destination.mkdir();modes=p.checked_tree(source,destination)
  self.assertEqual(modes,{'data.txt':0o640});self.assertEqual(p.fingerprint(source),p.fingerprint(destination))
  (source/'data.txt').write_bytes(b'x'*200001)
  with self.assertRaises(ValueError):p.checked_tree(source)
 def fixture(self):
  source=self.source();(source/'sub').mkdir();(source/'sub/run.py').write_text('print(1)\n');(source/'sub/run.py').chmod(0o755)
  repo=self.root/'repo';p.initialize_repository(source,repo)
  acceptance=self.root/'acceptance';acceptance.mkdir();(acceptance/'check.py').write_text('pass\n')
  def worker(workspace,*args):
   (workspace/'data.txt').chmod(0o640);(workspace/'sub').chmod(0o750);(workspace/'sub/run.py').chmod(0o755);return {'summary':'controlled'}
  factory=p.PilotFactory(self.root/'factory',worker,lambda *a:{'passed':True})
  self.addCleanup(factory.db.close)
  task=self.root/'task.json';p.save(task,{'objective':'controlled','repo':str(repo),'acceptance':str(acceptance),'checks':[['true']],'review_required':False})
  with patch.dict(os.environ,p.git_environment(),clear=True):
   first=factory.create(task);factory.resume(first);handoff=p.checkpoint(factory,first,self.root/'checkpoint')
   data=json.loads(task.read_text());data['repo']=str(self.root/'checkpoint');p.save(task,data);second=factory.create(task)
  return factory,first,second,Path(factory.status(first)['workspace']),handoff
 def test_pending_mode_restore_exact_and_prior_good_unchanged(self):
  factory,first,second,source,receipt=self.fixture();before=p.fingerprint(source);modes=p.checked_tree(source)
  status=factory.status(second);contract=(Path(status['directory'])/'task.json').read_bytes()
  result=p.restore_checkpoint(factory,second,source,receipt)
  self.assertEqual(result['after'],receipt['candidate']);self.assertEqual(result['mode_map_sha256'],p.digest(p.encoded(modes)))
  self.assertEqual(p.checked_tree(Path(status['workspace'])),modes);self.assertEqual(p.fingerprint(source),before);self.assertEqual(factory.status(first)['status'],'accepted')
  self.assertEqual((Path(status['directory'])/'task.json').read_bytes(),contract)
 def test_restore_wrong_bytes_exec_or_set_refuses_before_chmod(self):
  factory,first,second,source,receipt=self.fixture();target=Path(factory.status(second)['workspace']);original=(target/'data.txt').read_bytes();mode=(target/'data.txt').stat().st_mode
  for variant in ['bytes','extra','exec']:
   with self.subTest(variant=variant):
    if variant=='bytes':(target/'data.txt').write_text('changed')
    elif variant=='extra':(target/'extra').write_text('x')
    else:(target/'data.txt').chmod(0o755)
    before={str(x.relative_to(target)):x.stat().st_mode for x in target.rglob('*')}
    with self.assertRaises(ValueError):p.restore_checkpoint(factory,second,source,receipt)
    self.assertEqual(before,{str(x.relative_to(target)):x.stat().st_mode for x in target.rglob('*')})
    (target/'data.txt').write_bytes(original);(target/'data.txt').chmod(stat.S_IMODE(mode))
    if (target/'extra').exists():(target/'extra').unlink()
 def test_restore_nonpending_or_attempted_refuses(self):
  factory,first,second,source,receipt=self.fixture()
  for status,attempts in [('running',0),('pending',1),('accepted',1)]:
   with self.subTest(status=status):
    with patch.object(factory,'status',return_value={'status':status,'attempts':attempts}):
     with self.assertRaises(ValueError):p.restore_checkpoint(factory,second,source,receipt)
 def test_snapshot_rejects_git_controls_before_index(self):
  factory,first,second,source,receipt=self.fixture();target=Path(factory.status(second)['workspace']);(target/'.gitattributes').write_text('* filter=owned')
  with patch.object(factory,'_snapshot_git') as git:
   with self.assertRaises(ValueError):factory._index(Path(factory.status(second)['directory']),target)
   git.assert_not_called()
 def test_classification_strict_types_and_identity(self):
  identity={'running':True,'id':'fixed'};slot={'id':0,'n_ctx':98304,'is_processing':False}
  self.assertEqual(p.classify_idle({'status':'ok'},[slot],identity,identity,identity)['state'],'idle')
  busy=dict(slot,is_processing=True);self.assertEqual(p.classify_idle({'status':'ok'},[busy],identity,identity,identity)['state'],'busy')
  bads=[[],[slot,slot],[None],{},[dict(slot,id=False)],[dict(slot,n_ctx=98304.0)]]
  bads +=[[dict(slot,is_processing=x)] for x in [None,0,1,'false']]
  bads +=[[{k:v for k,v in slot.items() if k!='is_processing'}]]
  for slots in bads:
   with self.subTest(slots=slots):
    with self.assertRaises(ValueError):p.classify_idle({'status':'ok'},slots,identity,identity,identity)
  for changed in [{'running':1,'id':'fixed'},{'running':True,'id':'changed'}]:
   with self.assertRaises(ValueError):p.classify_idle({'status':'ok'},[slot],identity,changed,identity)
  with self.assertRaises(ValueError):p.classify_idle({'status':'loading'},[slot],identity,identity,identity)
 def test_cleanup_uncertainty_even_after_empty_queries(self):
  work=self.root/'factory/run/workspace';work.mkdir(parents=True);(self.root/'executor-uncertain.json').write_text('{}')
  with patch.object(p.subprocess,'run',return_value=SimpleNamespace(stdout=b'')) as run:
   with self.assertRaises(ValueError):p.cleanup_owned(self.root,time.monotonic()+10)
   self.assertEqual(run.call_count,2)
  (self.root/'executor-uncertain.json').unlink()
  with patch.object(p.subprocess,'run',side_effect=[SimpleNamespace(stdout=b'a'*12+b'\n'),SimpleNamespace(stdout=b''),SimpleNamespace(stdout=b'')]) as run:
   result=p.cleanup_owned(self.root,time.monotonic()+10)
   self.assertTrue(result[0]['confirmed_absent']);self.assertEqual(run.call_args_list[1].args[0],['docker','rm','-f','a'*12])
 def test_missing_create_attestation_sticky_fence(self):
  for code in [0,1,2,124,125,130]:
   with self.subTest(code=code):
    arm=self.root/str(code);arm.mkdir();sandbox=p.PilotSandbox(arm,time.monotonic()+10)
    with patch.object(p.Sandbox,'execute',return_value={'exit_code':code,'timed_out':code==124}):
     with self.assertRaises(RuntimeError):sandbox.execute(arm/'workspace',['true'])
     self.assertTrue((arm/'executor-uncertain.json').exists())
    with patch.object(p.Sandbox,'execute') as operation:
     with self.assertRaises(RuntimeError):sandbox.execute(arm/'workspace',['true'])
     operation.assert_not_called()
 def test_attested_application_failure_requires_absence(self):
  for absent in [True,False]:
   with self.subTest(absent=absent):
    arm=self.root/str(absent);arm.mkdir();workspace=arm/'workspace';workspace.mkdir();sandbox=p.PilotSandbox(arm,time.monotonic()+10)
    def guard(args,name,timeout,inspect_path=None):
     self.assertIsNotNone(inspect_path)
     p.save(inspect_path,{'name':name,'image':sandbox.image})
     return {'exit_code':1,'timed_out':False,'output':'ordinary controlled failure','elapsed_s':0}
    with patch.object(p.sandbox_module,'guarded_run',side_effect=guard),patch.object(p,'absent_workspace',side_effect=None if absent else ValueError('uncertain')) as check:
     if absent:self.assertEqual(sandbox.execute(workspace,['false'])['exit_code'],1)
     else:
      with self.assertRaises(RuntimeError):sandbox.execute(workspace,['false'])
     check.assert_called_once();self.assertEqual((arm/'executor-uncertain.json').exists(),not absent)
 def test_probe_bounded_output_nonzero_and_malformed_refuse(self):
  for raw,code in [(b'{}',0),(b'not-json',0),(b'x'*65537,0),(b'{"state":"idle"}',1)]:
   with self.subTest(size=len(raw),code=code):
    def spawn(*a,**kw):
     kw['stdout'].write(raw);kw['stdout'].flush()
     return SimpleNamespace(wait=lambda **k:None,returncode=code,pid=999999)
    with patch.object(p.subprocess,'Popen',side_effect=spawn):
     self.assertEqual(p.strict_probe('no-config','no-identity',time.monotonic()+2)['state'],'unknown')
 def test_probe_expired_deadline_no_subprocess(self):
  with patch.object(p.subprocess,'Popen') as launch:
   self.assertEqual(p.strict_probe('x','y',time.monotonic()-1)['state'],'unknown');launch.assert_not_called()
 def test_parent_cancellation_at_publication_never_accepts(self):
  args=SimpleNamespace(manifest='controlled',manifest_sha256='fixed',output=str(self.root/'pilot'),
      config='controlled',identity='controlled',bindings='controlled',lease=self.root/'lease')
  manifest={'cases':[{'id':'controlled'},{'id':'unused'}]}
  sync=os.fsync
  def cancel_at_sync(fd):
   sync(fd)
   if os.readlink('/proc/self/fd/'+str(fd)).endswith('/result.pending'):os.kill(os.getpid(),signal.SIGTERM)
  def supervisor(*a,**k):
   return {'stop':None,'client_group_absent':True,'exit_code':0,'work_finished_before_deadline':True,'cleanup_deadline':time.monotonic()+10}
  handlers={s:signal.getsignal(s) for s in [signal.SIGINT,signal.SIGTERM]}
  try:
   with ExitStack() as stack:
    for name,value in [('check_manifest',lambda *a:manifest),('wait_idle',lambda *a:True),('supervise',supervisor),('cleanup_owned',lambda *a:[]),('final_integrity',lambda *a:True)]:stack.enter_context(patch.object(p,name,value))
    stack.enter_context(patch.object(p.os,'fsync',side_effect=cancel_at_sync))
    stack.enter_context(patch.object(p,'ORDER',[(0,'direct')]))
    result=p.run_pilot(args)
   self.assertNotEqual(result[0]['status'],'accepted','Cancellation before result persistence must fence acceptance')
  finally:
   for sig,handler in handlers.items():signal.signal(sig,handler)

 def test_publication_deadline_after_fsync_and_conforming_control(self):
  result={'status':'accepted','candidate':'controlled'};target=self.root/'result.json';sync=os.fsync
  deadline=time.monotonic()+.02
  def delay(fd):sync(fd);time.sleep(.03)
  with patch.object(p.os,'fsync',side_effect=delay):published=p.publish_result(target,result,deadline,lambda:False)
  self.assertEqual(published['status'],'failed');self.assertEqual(json.loads(target.read_text()),published)
  self.assertEqual(result['status'],'accepted')
  good=p.publish_result(self.root/'good.json',result,time.monotonic()+2,lambda:False)
  self.assertEqual(good['status'],'accepted');self.assertEqual(json.loads((self.root/'good.json').read_text()),good)

 def test_cleanup_daemon_failure_or_bad_ids_refuse(self):
  (self.root/'factory/run/workspace').mkdir(parents=True)
  for outcome in [SimpleNamespace(stdout=b'not-an-id'),subprocess.TimeoutExpired('controlled',1)]:
   with self.subTest(outcome=type(outcome).__name__),patch.object(p.subprocess,'run',**({'side_effect':outcome} if isinstance(outcome,Exception) else {'return_value':outcome})):
    with self.assertRaises((ValueError,subprocess.TimeoutExpired)):p.cleanup_owned(self.root,time.monotonic()+2)

if __name__=='__main__':unittest.main(verbosity=2)
