"""Independent unit09 controls. Fake HTTP/guardian only; no model or Docker."""
import json
from contextlib import ExitStack
import os
from pathlib import Path
import sys
import signal
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import executable_review_prototype as p

CONFIG = {'endpoint': 'http://127.0.0.1:18000', 'model': 'flash-next-coder', 'reasoning': 'medium'}
GOOD = {'decision': 'pass', 'findings': [], 'question': ''}

class SecurityControls(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.case = self.root/'case'; self.case.mkdir()
        self.source = self.root/'source'; self.source.mkdir()
        (self.source/'main.py').write_text('value = 1\n')
        p.CaseLedger.create(self.case, time.monotonic()+300)
        self.ledger = p.CaseLedger(self.case)

    def test_failed_transport_is_debited_before_call_and_ninth_never_runs(self):
        observed = []
        def request(*args, **kwargs):
            observed.append(len(p.CaseLedger(self.case).read()['requests']))
            self.assertTrue((self.case/'requests'/f'{len(observed):02d}'/'request.json').exists())
            raise OSError('controlled transport failure')
        for _ in range(8):
            client = p.ReviewClient(CONFIG, p.CaseLedger(self.case), SimpleNamespace(request=request))
            with self.assertRaises(OSError): client.complete([])
        with self.assertRaises(RuntimeError): client.complete([])
        self.assertEqual(observed, list(range(1,9)))
        self.assertEqual([v['status'] for v in self.ledger.read()['requests']], ['failed']*8)
        self.assertFalse((self.case/'requests'/'09').exists())

    def test_malformed_transport_output_consumes_credit(self):
        client = p.ReviewClient(CONFIG, self.ledger, SimpleNamespace(request=lambda *a, **k: None))
        self.assertIsNone(client.complete([]))
        self.assertEqual(len(p.CaseLedger(self.case).read()['requests']), 1)

    def test_expired_or_over_capacity_request_never_dispatches(self):
        calls=[]
        client=p.ReviewClient(CONFIG,self.ledger,SimpleNamespace(request=lambda *a,**k:calls.append(1)))
        with self.assertRaises(ValueError):client.complete([{'content':'x'*(p.REQUEST_BYTES+1)}])
        with patch.object(p.time,'monotonic',return_value=self.ledger.read()['deadline']+1):
            with self.assertRaises(TimeoutError):client.complete([])
        self.assertEqual(calls,[]);self.assertEqual(self.ledger.read()['requests'],[])

    def executor(self):
        return p.CommandExecutor(self.case,self.source,{},self.ledger)

    def test_created_but_never_started_cannot_attest_execution(self):
        reached=[]
        def failed_start(args,name,timeout,inspect_path,**kwargs):
            reached.append(True)
            p.save(inspect_path,{'name':name,'image':'sha256:controlled'})
            return {'exit_code':1,'timed_out':False,'output':'Docker start failed before command execution','elapsed_s':0.01}
        with patch.object(p,'resolve_binding',return_value=SimpleNamespace(image='sha256:controlled',dependencies=self.root/'deps')), patch.object(p,'guarded_run',side_effect=failed_start), patch.object(p,'remove_owned',return_value={'confirmed_absent':True}):
            with self.assertRaises(RuntimeError):self.executor().run('true')
        self.assertEqual(reached,[True])
        self.assertEqual(self.ledger.read()['commands'][0]['error_type'],'RuntimeError')
        self.assertNotEqual(self.ledger.read()['commands'][0]['status'],'attested')

    def run_started(self,*,exit_code=1,body=b'actual command failed\n',receipt_change=None,cleanup_error=False):
        observed=[]
        def started(args,name,timeout,inspect_path,output,max_output_bytes):
            observed.append((args,timeout,max_output_bytes))
            nonce=args[-2]
            output.write((nonce+'\n').encode()+body)
            receipt={'name':name,'image':'sha256:controlled','host':{'Runtime':'runc','NetworkMode':'none','ReadonlyRootfs':True,'CapDrop':['ALL'],'Devices':[],'DeviceRequests':[],
                     'SecurityOpt':['no-new-privileges'],'Memory':1073741824,'MemorySwap':1073741824,'NanoCpus':2000000000,'PidsLimit':128,'ShmSize':16777216,'Tmpfs':{'/tmp':'rw,nosuid,nodev,size=128m'}},
                     'config':{'User':f'{os.getuid()}:{os.getgid()}','WorkingDir':'/candidate'},'mounts':[{'Source':str(self.source),'Destination':'/candidate','RW':False,'Type':'bind'},
                     {'Source':str(self.root/'deps'),'Destination':'/opt/deps','RW':False,'Type':'bind'}]}
            if receipt_change:receipt_change(receipt)
            p.save(inspect_path,receipt)
            return {'exit_code':exit_code,'timed_out':False,'output':'','elapsed_s':0.1}
        with patch.object(p,'resolve_binding',return_value=SimpleNamespace(image='sha256:controlled',dependencies=self.root/'deps')),patch.object(p,'guarded_run',side_effect=started),patch.object(p,'remove_owned',side_effect=RuntimeError('controlled absence uncertainty') if cleanup_error else None,return_value={'confirmed_absent':True}):
            result=self.executor().run('exit 1')
        return result,observed

    def test_actual_started_failure_is_valid_evidence_and_nonce_removed(self):
        result,observed=self.run_started()
        self.assertEqual(result['exit_code'],1);self.assertEqual(result['output'],'actual command failed\n')
        self.assertEqual(self.ledger.read()['commands'][0]['status'],'attested')
        self.assertTrue((self.case/'commands'/'01'/'started.json').exists())
        self.assertFalse((self.case/'executor-uncertain.json').exists())
        args,timeout,cap=observed[0]
        self.assertLessEqual(timeout,60);self.assertEqual(cap,16384+len(args[-2])+1)
        self.assertNotIn('/workspace',str(args));self.assertIn('none',args)
        self.assertIn('no-new-privileges',args)

    def test_started_writable_mount_cannot_attest(self):
        with self.assertRaises(RuntimeError):self.run_started(receipt_change=lambda receipt:receipt['mounts'][0].update(RW=True))
        self.assertTrue((self.case/'executor-uncertain.json').exists())

    def test_started_cleanup_uncertainty_cannot_attest(self):
        with self.assertRaises(RuntimeError):self.run_started(cleanup_error=True)
        self.assertTrue((self.case/'executor-uncertain.json').exists())
        self.assertEqual(self.ledger.read()['commands'][0]['status'],'uncertain')

    def test_missing_resource_limit_cannot_attest(self):
        with self.assertRaises(RuntimeError):self.run_started(receipt_change=lambda receipt:receipt['host'].update(Memory=0))
        self.assertTrue((self.case/'executor-uncertain.json').exists())

    def test_root_uid_refused_before_command_debit_or_dispatch(self):
        with patch.object(p.os,'getuid',return_value=0),patch.object(p,'guarded_run') as guard:
            with self.assertRaises(RuntimeError):self.executor().run('true')
        guard.assert_not_called();self.assertEqual(self.ledger.read()['commands'],[])

    def test_missing_creation_is_sticky_even_after_empty_absence(self):
        calls=[]
        def no_receipt(*args,**kwargs):
            calls.append(1)
            return {'exit_code':0,'timed_out':False,'output':'pretend success','elapsed_s':0}
        with patch.object(p,'resolve_binding',return_value=SimpleNamespace(image='sha256:controlled',dependencies=self.root/'deps')), patch.object(p,'guarded_run',side_effect=no_receipt), patch.object(p,'remove_owned',return_value={'confirmed_absent':True}):
            executor=self.executor()
            with self.assertRaises(RuntimeError):executor.run('true')
            with self.assertRaises(RuntimeError):executor.run('true')
        self.assertEqual(calls,[1]);self.assertTrue((self.case/'executor-uncertain.json').exists())
        self.assertEqual(len(self.ledger.read()['commands']),1)

    def test_candidate_links_and_special_types_rejected(self):
        victim=self.root/'victim';victim.write_text('outside')
        for kind in ['symlink','hardlink','fifo']:
            with self.subTest(kind=kind):
                path=self.source/'bad'
                if kind=='symlink':path.symlink_to(victim)
                elif kind=='hardlink':os.link(victim,path)
                else:os.mkfifo(path)
                try:
                    with self.assertRaises(ValueError):p.tree_facts(self.source)
                finally:path.unlink()

    def test_no_command_verdict_refused_and_tool_data_not_policy(self):
        final={'choices':[{'finish_reason':'stop','message':{'role':'assistant','content':json.dumps(GOOD)}}]}
        with self.assertRaises(ValueError):
            p.review_case(self.case,'controlled',self.source,SimpleNamespace(complete=lambda m:final),None,self.ledger)
        self.assertFalse((self.case/'verdict.json').exists())
        self.assertIn('untrusted evidence',p.SYSTEM)
        self.assertNotIn('Do not execute tools',p.SYSTEM)

    def batch_control(self, idle=(True,True), cleanup_error=False, publication_cancel=False, publication_deadline=False):
        output=self.root/'batch'
        args=SimpleNamespace(manifest=self.root/'manifest',manifest_sha256='controlled',output=output,
             config=self.root/'config',identity=self.root/'identity',bindings=self.root/'bindings',lease=self.root/'lease')
        cases={'cases':[{'id':'case-01'},{'id':'case-02'}]}
        launches=[]
        idle_values=iter(idle)
        def supervisor(command,log,deadline,cancelled):
            case=Path(command[-1]).parent;launches.append(case.name)
            candidate=case/'candidate';candidate.mkdir();(candidate/'main.py').write_text('value = 1\n')
            facts=p.tree_facts(candidate)
            p.save(case/'input.json',{'facts':facts})
            p.save(case/'child-result.json',{'status':'accepted','verdict':GOOD,'attested_commands':1,'candidate_sha256':p.digest(p.encoded(facts))})
            return {'cleanup_deadline':time.monotonic()+150,'stop':None,'exit_code':0,'client_group_absent':True,'work_finished_before_deadline':True}
        original_fsync=os.fsync
        injected=[]
        def fsync(fd):
            original_fsync(fd)
            if os.readlink('/proc/self/fd/'+str(fd)).endswith('/result.pending') and not injected:
                injected.append(True)
                if publication_cancel:os.kill(os.getpid(),signal.SIGTERM)
                if publication_deadline:clock.return_value=time.monotonic()+301
        handlers={s:signal.getsignal(s) for s in (signal.SIGINT,signal.SIGTERM)}
        try:
            with ExitStack() as stack:
                stack.enter_context(patch.object(p,'verify_manifest',return_value=cases))
                stack.enter_context(patch.object(p,'wait_idle',side_effect=lambda *a,**k:next(idle_values,False)))
                stack.enter_context(patch.object(p,'supervise',side_effect=supervisor))
                stack.enter_context(patch.object(p,'cleanup_case',side_effect=RuntimeError('controlled uncertainty') if cleanup_error else None,return_value=[]))
                stack.enter_context(patch.object(os,'fsync',side_effect=fsync))
                original_clock=time.monotonic
                clock=stack.enter_context(patch.object(time,'monotonic',side_effect=lambda:original_clock()))
                if publication_deadline:
                    # Set side_effect to None only at the final publication boundary.
                    def deadline_sync(fd):
                        original_fsync(fd)
                        if os.readlink('/proc/self/fd/'+str(fd)).endswith('/result.pending') and not injected:
                            injected.append(True);clock.side_effect=None;clock.return_value=original_clock()+301
                    stack.enter_context(patch.object(os,'fsync',side_effect=deadline_sync))
                results=p.batch(args)
        finally:
            for signum,handler in handlers.items():signal.signal(signum,handler)
        return launches,results,output

    def test_unknown_idle_admission_prevents_case_dispatch(self):
        launches,results,_=self.batch_control(idle=(False,))
        self.assertEqual(launches,[]);self.assertEqual(results[0]['status'],'not_started')

    def test_unknown_postcase_idle_prevents_next_case(self):
        launches,results,_=self.batch_control(idle=(True,False))
        self.assertEqual(launches,['case-01']);self.assertNotEqual(results[0]['status'],'accepted')

    def test_cleanup_uncertainty_stops_next_case(self):
        launches,results,_=self.batch_control(cleanup_error=True)
        self.assertEqual(launches,['case-01']);self.assertFalse(results[0]['cleanup_confirmed'])
        self.assertNotEqual(results[0]['status'],'accepted')

    def test_actual_signal_at_publication_fsync_refuses_success(self):
        launches,results,output=self.batch_control(publication_cancel=True)
        self.assertEqual(launches,['case-01']);self.assertEqual(results[0]['status'],'failed')
        self.assertEqual(json.loads((output/'case-01'/'result.json').read_bytes())['status'],'failed')

    def test_deadline_at_publication_fsync_refuses_success(self):
        _,results,output=self.batch_control(publication_deadline=True)
        self.assertEqual(results[0]['status'],'failed')
        self.assertEqual(json.loads((output/'case-01'/'result.json').read_bytes())['status'],'failed')

    def test_conforming_completed_control_publishes(self):
        launches,results,_=self.batch_control()
        self.assertEqual(launches,['case-01']);self.assertEqual(results[0]['status'],'accepted')

if __name__=='__main__':unittest.main(verbosity=2)
