"""Independent cancellation-driver controls: fake probes and owned local clients only."""
import argparse
from contextlib import ExitStack
import fcntl
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cancellation_probe as c

POPEN, SLEEP = subprocess.Popen, time.sleep

class CancellationControls(unittest.TestCase):
    def trial(self, states, *, normal=False, during=None, main=False, real_timing=False):
        temporary = tempfile.TemporaryDirectory(); self.addCleanup(temporary.cleanup)
        root = Path(temporary.name); out = root/'result'; lease = root/'lease'
        args = argparse.Namespace(admission=str(root/'admission'), output=str(out),
                                  config=str(root/'config'), identity=str(root/'identity'), lease=str(lease))
        Path(args.admission).write_text('{}')
        children=[]; seen=[]; sequence=iter(states)
        def locked():
            if not main:return
            with lease.open('a') as stream:
                with self.assertRaises(BlockingIOError):
                    fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        def probe(*a):
            locked(); value=next(sequence, 'idle'); seen.append(value)
            if during:during('probe', out, len(seen))
            if value=='normal':
                (out/'response.json').write_text('{}')
                children[0].terminate(); children[0].wait(timeout=2)
                value='busy'
            if value=='deadline':
                SLEEP(.05); value='busy'
            return {'state':value,'reason':'controlled'}
        def spawn(*a, **kw):
            if during:during('launch', out, 0)
            child=POPEN([sys.executable,'-c','import time; time.sleep(30)'],
                        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,start_new_session=True)
            children.append(child); return child
        saved=c.save
        def save(path,value):
            saved(path,value)
            if during:during(path.name,out,0)
        def cleanup():
            for child in children:
                if child.poll() is None:
                    os.killpg(child.pid,signal.SIGKILL);child.wait(timeout=2)
        self.addCleanup(cleanup)
        with ExitStack() as stack:
            stack.enter_context(patch.object(c,'validate_admission',return_value={}))
            stack.enter_context(patch.object(c,'strict_probe',side_effect=probe))
            stack.enter_context(patch.object(c.subprocess,'Popen',side_effect=spawn))
            stack.enter_context(patch.object(c.time,'sleep',side_effect=lambda t:SLEEP(t if real_timing else min(t,.005))))
            stack.enter_context(patch.object(c,'save',side_effect=save))
            stack.enter_context(patch.object(c,'WORK_SECONDS',.04 if 'deadline' in states else 5))
            stack.enter_context(patch.object(c,'CLEANUP_SECONDS',4 if real_timing else .2))
            if main:
                stack.enter_context(patch.object(sys,'argv',['probe','--config',args.config,'--output',args.output,
                    '--identity',args.identity,'--lease',args.lease,'--admission',args.admission]))
                c.main();result=json.loads((out/'result.json').read_text())
            else:result=c.experiment(args)
        return result,children,seen,out

    def test_observed_busy_then_signal_and_idle_passes(self):
        result,children,seen,out=self.trial(['idle','idle','busy','idle','idle'])
        self.assertEqual(result['outcome'],'passed');self.assertEqual(result['charged_requests'],1)
        self.assertTrue(result['cleanup']['group_absent']);self.assertEqual(children[0].returncode,-signal.SIGTERM)

    def test_real_idle_spacing(self):
        result,children,seen,out=self.trial(['idle','idle','busy','idle','idle'],real_timing=True)
        self.assertEqual(result['outcome'],'passed')
        events=json.loads((out/'events.json').read_text())
        samples=[e['elapsed_s'] for e in events if e['kind']=='cleanup_observation']
        self.assertGreaterEqual(samples[1]-samples[0],1)
        self.assertGreaterEqual(result['elapsed_s'],3)

    def test_consumed_admission_refuses_fresh_output(self):
        result,children,seen,out=self.trial(['idle','idle','busy','idle','idle'])
        root=out.parent
        args=argparse.Namespace(admission=str(root/'admission'),output=str(root/'again'),
            config=str(root/'config'),identity=str(root/'identity'),lease=str(root/'lease'))
        with patch.object(c,'validate_admission',return_value={}), patch.object(c,'strict_probe',return_value={'state':'idle'}), patch.object(c.time,'sleep'), patch.object(c.subprocess,'Popen') as launch:
            result=c.experiment(args)
            self.assertEqual(result['outcome'],'failed')
            self.assertEqual(result['error_type'],'FileExistsError')
            launch.assert_not_called()

    def test_group_descendant_cleanup(self):
        with tempfile.TemporaryDirectory() as folder:
            marker=Path(folder)/'pid'
            code="import subprocess,signal,sys,time; c=subprocess.Popen([sys.executable,'-c','import time;time.sleep(30)']); open(sys.argv[1],'w').write(str(c.pid)); signal.signal(signal.SIGTERM,lambda *a:(c.wait(),sys.exit(0))); time.sleep(30)"
            child=POPEN([sys.executable,'-c',code,str(marker)],start_new_session=True)
            try:
                until=time.monotonic()+2
                while not marker.exists() and time.monotonic()<until:SLEEP(.01)
                self.assertTrue(marker.exists());descendant=int(marker.read_text())
                result=c.stop_client(child,time.monotonic()+3)
                self.assertTrue(result['group_absent'])
                with self.assertRaises(ProcessLookupError):os.kill(descendant,0)
            finally:
                if child.poll() is None:os.killpg(child.pid,signal.SIGKILL);child.wait()

    def test_unknown_is_not_busy(self):
        result,*_=self.trial(['idle','idle','unknown','idle','idle'])
        self.assertNotEqual(result['outcome'],'passed');self.assertFalse(result['observed_busy'])

    def test_preflight_unknown_never_launches(self):
        result,children,*_=self.trial(['unknown'])
        self.assertEqual(result['charged_requests'],0);self.assertFalse(children)

    def test_normal_completion_race_inconclusive(self):
        result,*_=self.trial(['idle','idle','normal','idle','idle'])
        self.assertEqual(result['outcome'],'inconclusive')

    def test_deadline_during_busy_probe_not_pass(self):
        result,*_=self.trial(['idle','idle','deadline','idle','idle'])
        self.assertNotEqual(result['outcome'],'passed')

    def test_cancellation_during_busy_probe_not_pass(self):
        def signal_at_probe(kind,out,count):
            if kind=='probe' and count==3:os.kill(os.getpid(),signal.SIGTERM)
        result,*_=self.trial(['idle','idle','busy','idle','idle'],during=signal_at_probe)
        self.assertNotEqual(result['outcome'],'passed');self.assertTrue(result['cancelled'])

    def test_debit_cancellation_prevents_launch(self):
        def cancel_debit(kind,out,count):
            if kind=='debit.json':os.kill(os.getpid(),signal.SIGTERM)
        result,children,*_=self.trial(['idle','idle','idle','idle'],during=cancel_debit)
        self.assertFalse(children,'Cancellation after debit must not launch client')
        self.assertNotEqual(result['outcome'],'passed')

    def test_lease_held_during_preflight_and_cleanup(self):
        result,*_=self.trial(['idle','idle','busy','idle','idle'],main=True)
        self.assertEqual(result['outcome'],'passed')

    def test_unknown_cleanup_never_passes(self):
        result,*_=self.trial(['idle','idle','busy']+['unknown']*100)
        self.assertEqual(result['outcome'],'cleanup_unresolved')

    def test_stop_group_terminates_owned_client(self):
        child=POPEN([sys.executable,'-c','import time;time.sleep(30)'],start_new_session=True)
        try:
            result=c.stop_client(child,time.monotonic()+3)
            self.assertTrue(result['group_absent']);self.assertEqual(result['returncode'],-signal.SIGTERM)
        finally:
            if child.poll() is None:os.killpg(child.pid,signal.SIGKILL);child.wait()

    def test_request_error_does_not_expose_credentials(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder);cfg=p/'config';cfg.write_text(json.dumps({'model':c.BODY['model']}))
            secret='Bearer PRIVATE_SENTINEL_97531'
            with patch.object(c,'ModelWorker') as worker:
                worker.return_value.request.side_effect=RuntimeError(secret)
                self.assertEqual(c.request_child(cfg,p),2)
            self.assertNotIn(secret,(p/'client-complete.json').read_text())
            worker.return_value.request.assert_called_once()
            self.assertEqual(worker.return_value.request.call_args.kwargs['max_response_bytes'],1024*1024)

    def test_evidence_size_bound(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'x.json'
            with self.assertRaises(ValueError):c.save(p,{'x':'a'*(1024*1024)})
            self.assertFalse(p.exists())

    def test_admission_code_and_request_drift_refused(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);(root/'ops').mkdir()
            files={name:hashlib.sha256(b'fixed').hexdigest() for name in ['ops/cancellation_probe.py','ops/planning_pilot_prototype.py']}
            for name in files:(root/name).write_bytes(b'fixed')
            receipt={'approved':True,'experiment':'single-request-cancellation','prototype_files':files,
                     'request_sha256':hashlib.sha256(json.dumps(c.BODY,sort_keys=True).encode()).hexdigest()}
            identity=root/'identity.json';identity.write_text('{}')
            config=root/'config.json';config.write_text(json.dumps({'endpoint':'http://127.0.0.1:18000','model':'flash-next-coder','reasoning':'medium'}))
            contract=Path('/home/gradrix/repos/gflo/.scratch/.sflo/08-autonomy-planning-pilot/cancellation-probe-contract.md')
            evidence={}
            for kind in ['contract','controlled_tests','security_review']:
                source=contract if kind=='contract' else root/(kind+'.txt')
                if kind!='contract':source.write_text('controlled fixture')
                evidence[kind]={'path':str(source),'sha256':hashlib.sha256(source.read_bytes()).hexdigest()}
            receipt.update(lease_path=str(root/'lease'),evidence=evidence,identity_sha256=hashlib.sha256(identity.read_bytes()).hexdigest(),public_config=json.loads(config.read_text()))
            p=root/'admission.json';p.write_text(json.dumps(receipt))
            with patch.object(c,'ROOT',root):
                self.assertEqual(c.validate_admission(p,identity,config,root/'lease'),receipt)
                with self.assertRaises(ValueError):c.validate_admission(p,identity,config,root/'other-lease')
                for source in [identity, root/'controlled_tests.txt', root/'security_review.txt',config]:
                    original=source.read_bytes();source.write_bytes(original+b' ')
                    if source==config:
                        source.write_text(json.dumps({'endpoint':'http://127.0.0.1:1','model':'flash-next-coder','reasoning':'medium'}))
                    with self.assertRaises(ValueError):c.validate_admission(p,identity,config,root/'lease')
                    source.write_bytes(original)
                (root/'ops/cancellation_probe.py').write_bytes(b'changed')
                with self.assertRaises(ValueError):c.validate_admission(p,identity,config,root/'lease')
                (root/'ops/cancellation_probe.py').write_bytes(b'fixed')
                receipt['request_sha256']='0'*64;p.write_text(json.dumps(receipt))
                with self.assertRaises(ValueError):c.validate_admission(p,identity,config,root/'lease')

if __name__=='__main__':unittest.main(verbosity=2)
