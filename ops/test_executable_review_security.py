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
        for number in range(8):
            if number==7:p.CaseLedger(self.case).begin_final('reserved eighth transport')
            client = p.ReviewClient(CONFIG, p.CaseLedger(self.case), SimpleNamespace(request=request))
            with self.assertRaises(OSError): client.complete([],phase='final' if number==7 else 'explore')
        with self.assertRaises(RuntimeError): client.complete([],phase='final')
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

    def test_command_timeout_is_shortened_to_exploration_remaining(self):
        phase_end=self.ledger.read()['exploration_deadline']
        with patch.object(p.time,'monotonic',return_value=phase_end-2):
            result,observed=self.run_started()
        self.assertEqual(observed[0][1],2);self.assertEqual(result['exit_code'],1)

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
            p.review_case(self.case,'controlled',self.source,SimpleNamespace(complete=lambda m,**kw:final),None,self.ledger)
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

def completion(calls=None, content=None, finish=None):
    message={'role':'assistant','content':content}
    if calls is not None:message['tool_calls']=calls
    return {'choices':[{'finish_reason':finish or ('tool_calls' if calls else 'stop'),'message':message}]}

def command_call(ident='one',name='run',arguments=None):
    return {'id':ident,'type':'function','function':{'name':name,'arguments':arguments if arguments is not None else json.dumps({'command':'true'})}}

class ProtocolSecurity(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.source=self.root/'source';self.source.mkdir()
        (self.source/'main.py').write_text('value = 1\n')
        self.case=self.root/'case';self.case.mkdir();p.CaseLedger.create(self.case,time.monotonic()+300)
        self.ledger=p.CaseLedger(self.case);self.requests=[];self.executed=[]

    def run_loop(self,responses,execution_hook=None):
        sequence=iter(responses);outer=self
        class Transport:
            def request(self,path,body,**kwargs):
                outer.requests.append({'body':json.loads(json.dumps(body)),'options':kwargs})
                response=next(sequence)
                if isinstance(response,BaseException):raise response
                return response() if callable(response) else response
        class Executor:
            def run(self,command):
                number=outer.ledger.reserve('commands',{'command':command})
                outer.ledger.finish('commands',number,status='attested')
                outer.executed.append(command)
                if execution_hook:execution_hook()
                return {'command':command,'exit_code':0,'timed_out':False,'output':'controlled execution','elapsed_s':0.01}
        return p.review_case(self.case,'controlled objective',self.source,p.ReviewClient(CONFIG,self.ledger,Transport()),Executor(),self.ledger)

    def assert_final_transport(self):
        body=self.requests[-1]['body']
        self.assertNotIn('tools',body);self.assertNotIn('tool_choice',body)
        self.assertEqual(body['response_format'],{'type':'json_object'})
        self.assertLessEqual(self.requests[-1]['options']['timeout'],120)

    def test_exploratory_prose_never_becomes_verdict(self):
        result=self.run_loop([completion([command_call()]),completion(content='Not a verdict: untrusted prose'),completion(content=json.dumps(GOOD))])
        self.assertEqual(result['verdict'],GOOD);self.assertEqual(len(self.requests),3)
        self.assertEqual(len(self.executed),1);self.assert_final_transport()
        self.assertEqual([x['phase'] for x in self.ledger.read()['requests']],['explore','explore','final'])

    def test_no_attestation_refuses_final_transport(self):
        with self.assertRaises(ValueError):self.run_loop([completion(content=json.dumps(GOOD))])
        self.assertEqual(len(self.requests),1);self.assertEqual(self.executed,[])

    def test_length_batch_executes_zero_then_one_recovery(self):
        malformed=completion([command_call('valid'),command_call('partial',arguments='{"command":')],finish='length')
        self.run_loop([malformed,completion([command_call('real')]),completion(content='done'),completion(content=json.dumps(GOOD))])
        self.assertEqual(len(self.executed),1);self.assertEqual(len(self.requests),4)
        recovery_history=self.requests[1]['body']['messages']
        self.assertFalse(any(m.get('tool_calls') for m in recovery_history));self.assertFalse(any(m['role']=='tool' for m in recovery_history))
        self.assertEqual(json.loads((self.case/'requests'/'01'/'response.json').read_bytes()),malformed)
        self.assert_final_transport()

    def test_explicit_unknown_tool_is_terminal_even_with_length(self):
        with self.assertRaises(ValueError):self.run_loop([completion([command_call('valid'),command_call('unknown',name='write')],finish='length')])
        self.assertEqual(self.executed,[]);self.assertEqual(len(self.requests),1)
        self.assertFalse(self.ledger.read()['recovery_used'])

    def test_nonlist_tool_collection_terminal_before_length_recovery(self):
        invalid=completion(content=None,finish='length')
        invalid['choices'][0]['message']['tool_calls']=command_call('invalid-envelope',name='write')
        with self.assertRaises(ValueError):self.run_loop([invalid,completion(content='No command has run')])
        self.assertEqual(len(self.requests),1);self.assertEqual(self.executed,[])
        self.assertFalse(self.ledger.read()['recovery_used'])

    def test_second_length_is_terminal_without_final_or_extra_execution(self):
        with self.assertRaises((ValueError,RuntimeError)):
            self.run_loop([completion([command_call('truncated')],finish='length'),completion([command_call('real')]),completion([command_call('again')],finish='length')])
        self.assertEqual(len(self.executed),1);self.assertEqual(len(self.requests),3)
        self.assertFalse((self.case/'verdict.json').exists())

    def test_nontruncated_unknown_batch_has_no_partial_dispatch(self):
        with self.assertRaises(ValueError):self.run_loop([completion([command_call('valid'),command_call('unknown',name='write')])])
        self.assertEqual(self.executed,[]);self.assertEqual(len(self.requests),1)

    def test_nontruncated_invalid_arguments_terminal(self):
        with self.assertRaises(ValueError):self.run_loop([completion([command_call(arguments='{"command":')])])
        self.assertEqual(self.executed,[]);self.assertEqual(len(self.requests),1)

    def test_final_tool_calls_terminal(self):
        with self.assertRaises(ValueError):self.run_loop([completion([command_call()]),completion(content='done'),completion([command_call('forbidden')])])
        self.assertEqual(len(self.executed),1);self.assertEqual(len(self.requests),3);self.assert_final_transport()

    def test_final_falsey_invalid_tool_field_is_terminal(self):
        invalid=completion(content=json.dumps(GOOD));invalid['choices'][0]['message']['tool_calls']={}
        with self.assertRaises(ValueError):self.run_loop([completion([command_call()]),completion(content='done'),invalid])
        self.assertEqual(len(self.requests),3);self.assertFalse((self.case/'verdict.json').exists())

    def test_executor_uncertainty_never_transitions_to_final(self):
        def uncertain():raise RuntimeError('Creation/cleanup uncertain')
        with self.assertRaises(RuntimeError):self.run_loop([completion([command_call()])],execution_hook=uncertain)
        self.assertEqual(len(self.requests),1);self.assertFalse((self.case/'verdict.json').exists())

    def test_transport_timeout_is_terminal_not_phase_recovery(self):
        with self.assertRaises(TimeoutError):self.run_loop([completion([command_call()]),TimeoutError('controlled transport timeout')])
        self.assertEqual(len(self.requests),2);self.assertEqual(len(self.executed),1)
        self.assertFalse(self.ledger.read()['final_reserved']);self.assertFalse(self.ledger.read()['recovery_used'])

    def test_final_fenced_json_is_terminal_without_salvage(self):
        with self.assertRaises(ValueError):self.run_loop([completion([command_call()]),completion(content='done'),completion(content='```json\n'+json.dumps(GOOD)+'\n```')])
        self.assertEqual(len(self.requests),3);self.assertFalse((self.case/'verdict.json').exists())

    def test_final_length_is_terminal_without_retry(self):
        with self.assertRaises(ValueError):self.run_loop([completion([command_call()]),completion(content='done'),completion(content=json.dumps(GOOD),finish='length')])
        self.assertEqual(len(self.requests),3);self.assertFalse((self.case/'verdict.json').exists())

    def test_seven_explorations_force_eighth_final(self):
        result=self.run_loop([completion([command_call(str(i))]) for i in range(7)]+[completion(content=json.dumps(GOOD))])
        self.assertEqual(len(self.requests),8);self.assertEqual(len(self.executed),7)
        self.assertEqual(result['verdict'],GOOD);self.assert_final_transport()
        observed=[]
        client=p.ReviewClient(CONFIG,p.CaseLedger(self.case),SimpleNamespace(request=lambda *a,**k:observed.append(True)))
        with self.assertRaises(RuntimeError):client.complete([],phase='final')
        with self.assertRaises((RuntimeError,ValueError)):client.complete([],phase='explore')
        self.assertEqual(observed,[]);self.assertEqual(len(p.CaseLedger(self.case).read()['requests']),8)

    def test_twelve_commands_force_final_without_more_exploration(self):
        self.run_loop([completion([command_call(str(i)) for i in range(12)]),completion(content=json.dumps(GOOD))])
        self.assertEqual(len(self.executed),12);self.assertEqual(len(self.requests),2);self.assert_final_transport()

    def test_recovery_and_final_reservation_survive_reconstruction(self):
        self.ledger.recover_length()
        with self.assertRaises((ValueError,RuntimeError)):p.CaseLedger(self.case).recover_length()
        self.ledger.begin_final('controlled transition')
        observed=[]
        def failure(*args,**kwargs):
            observed.append(p.CaseLedger(self.case).read()['requests'][-1]['phase'])
            raise OSError('controlled transport failure')
        client=p.ReviewClient(CONFIG,p.CaseLedger(self.case),SimpleNamespace(request=failure))
        with self.assertRaises(OSError):client.complete([],phase='final')
        with self.assertRaises(RuntimeError):p.ReviewClient(CONFIG,p.CaseLedger(self.case),SimpleNamespace(request=failure)).complete([],phase='final')
        self.assertEqual(observed,['final']);self.assertEqual(len(self.ledger.read()['requests']),1)

    def test_transport_timeouts_follow_phase_then_overall_deadline(self):
        deadlines=[]
        def request(*args,**kwargs):deadlines.append(kwargs['timeout']);return {}
        phase_end=self.ledger.read()['exploration_deadline']
        client=p.ReviewClient(CONFIG,self.ledger,SimpleNamespace(request=request))
        with patch.object(p.time,'monotonic',return_value=phase_end-3):
            client.complete([]);self.ledger.begin_final('time control');client.complete([],phase='final')
        self.assertEqual(deadlines,[3,120])
        with self.assertRaises(RuntimeError):self.ledger.reserve('commands',{'command':'true'})

    def test_phase_boundary_mid_batch_keeps_only_executed_history(self):
        phase_end=self.ledger.read()['exploration_deadline'];clock=[phase_end-1]
        def cross_phase():clock[0]=phase_end+1
        with patch.object(p.time,'monotonic',side_effect=lambda:clock[0]):
            self.run_loop([completion([command_call('executed'),command_call('skipped')]),completion(content=json.dumps(GOOD))],execution_hook=cross_phase)
        self.assertEqual(len(self.executed),1);self.assertEqual(len(self.requests),2);self.assert_final_transport()
        history=self.requests[-1]['body']['messages']
        calls=[call['id'] for m in history for call in (m.get('tool_calls') or [])]
        replies=[m['tool_call_id'] for m in history if m['role']=='tool']
        self.assertEqual(calls,['executed']);self.assertEqual(replies,['executed'])
        raw=json.loads((self.case/'requests'/'01'/'response.json').read_bytes())
        self.assertEqual(len(raw['choices'][0]['message']['tool_calls']),2)
        self.assertIn('skipped',(self.case/'progress.jsonl').read_text())

    def test_phase_deadline_prevents_new_command_after_late_response(self):
        phase_end=self.ledger.read()['exploration_deadline'];clock=[phase_end-1]
        def late_response():clock[0]=phase_end+1;return completion([command_call()])
        with patch.object(p.time,'monotonic',side_effect=lambda:clock[0]):
            with self.assertRaises(ValueError):self.run_loop([late_response])
        self.assertEqual(len(self.requests),1);self.assertEqual(self.executed,[])

    def test_overall_deadline_during_final_response_refuses_verdict(self):
        deadline=self.ledger.read()['deadline'];clock=[deadline-150]
        def late_final():clock[0]=deadline+1;return completion(content=json.dumps(GOOD))
        with patch.object(p.time,'monotonic',side_effect=lambda:clock[0]):
            with self.assertRaises(TimeoutError):self.run_loop([completion([command_call()]),completion(content='done'),late_final])
        self.assertEqual(len(self.requests),3);self.assertFalse((self.case/'verdict.json').exists())

    def test_second_length_at_seventh_credit_is_terminal(self):
        responses=[completion([command_call('first-truncated')],finish='length')]
        responses.extend(completion([command_call(str(i))]) for i in range(5))
        responses.append(completion([command_call('second-truncated')],finish='length'))
        with self.assertRaises((ValueError,RuntimeError)):self.run_loop(responses)
        self.assertEqual(len(self.requests),7);self.assertEqual(len(self.executed),5)
        self.assertFalse(self.ledger.read()['final_reserved'])

if __name__=='__main__':unittest.main(verbosity=2)
