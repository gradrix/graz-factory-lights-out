import copy
import json
import os
import shutil
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock
sys.path.insert(0,str(Path(__file__).resolve().parent))
import review_evidence_prototype as p

REPO=Path(__file__).resolve().parents[1]
PUBLIC=REPO/'evaluations/executable-review/manifest.json'
TRIAL=Path('/home/gradrix/repos/gflo/.gflo/executable-review-protocol-trial-1/artifact-hashes.json')
CONFIG={'endpoint':'http://127.0.0.1:18000','model':'flash-next-coder','reasoning':'medium'}


def payload():
    return {'objective':'Tests required.\n\nDocs needed.\n','objective_lines':['Tests required.','','Docs needed.'],
            'files':{'test.py':'bad()\nok()\n'},
            'catalog':{'commands':[{'id':1,'command':'python -m unittest','exit_code':0}],
                       'segments':[{'id':1,'command_id':1,'text':'FAILED (errors=1)'},{'id':2,'command_id':1,'text':'OK'}]}}


def finding(**over):
    value={'severity':'major','source':{'path':'test.py','line':1},'requirements':[1],'observations':[1],'inference':'Suite fails.'}
    value.update(over);return value


def diagnosis(*findings,decision='repair',question=''):
    return {'version':1,'decision':decision,'findings':list(findings),'question':question}


class FakeTransport:
    def __init__(self,content=None,error=None):
        self.calls=[];self.content=content;self.error=error
    def request(self,path,body,timeout,max_response_bytes):
        self.calls.append({'path':path,'body':body,'timeout':timeout})
        if self.error:raise self.error
        return {'choices':[{'finish_reason':'stop','message':{'role':'assistant','content':self.content}}],'usage':{'total_tokens':1}}


class EvidenceTests(unittest.TestCase):
    def test_exact_segments(self):
        text='a'*2047+'\n😀\\"'+ '�'*2500
        parts=p.split_segments(text)
        self.assertEqual(''.join(parts),text)
        self.assertTrue(all(len(p.encoded(s))<=2048 for s in parts))

    def test_inference_is_not_entailment(self):
        v=diagnosis(finding(inference='All tests passed after repair.'))
        report=p.validate_diagnosis(v,payload())
        self.assertEqual(report['findings'][0]['observations'][0]['text'],'FAILED (errors=1)')
        self.assertEqual(report['findings'][0]['inference'],v['findings'][0]['inference'])
        v['findings'][0]['observations']=[True]
        with self.assertRaises(ValueError):p.validate_diagnosis(v,payload())

    def test_schema_reference_and_capacity_bounds(self):
        bad=[diagnosis(finding(requirements=[2])),                      # blank objective line
             diagnosis(finding(requirements=[4])),
             diagnosis(finding(requirements=[1,1])),
             diagnosis(finding(requirements=[True])),
             diagnosis(finding(observations=[3])),
             diagnosis(finding(observations=[])),                       # blocking needs evidence
             diagnosis(finding(source={'path':'test.py','line':3})),
             diagnosis(finding(source={'path':'other.py','line':1})),
             diagnosis(finding(source={'path':'test.py','line':True})),
             diagnosis(finding(inference='x'*1025)),
             diagnosis(finding(inference=' ')),
             diagnosis({**finding(),'repair':'add test'}),
             diagnosis(finding(severity='minor',observations=[])),     # repair without blocking finding
             diagnosis(finding(),decision='pass'),
             diagnosis(decision='needs_input'),
             diagnosis(question='why?',decision='pass'),
             diagnosis(*[finding(severity='minor',observations=[1,2])]*9,decision='pass'),
             {**diagnosis(finding()),'version':True},
             {**diagnosis(finding()),'summary':'all good'}]
        for value in bad:
            with self.subTest(value=value),self.assertRaises(ValueError):p.validate_diagnosis(value,payload())
        many=[{'id':n,'command_id':1,'text':str(n)} for n in range(1,9)]
        data=payload();data['catalog']['segments']=many
        over=diagnosis(*[finding(observations=[1,2,3,4])]*7)
        with self.assertRaises(ValueError):p.validate_diagnosis(over,data)
        p.validate_diagnosis(diagnosis(*[finding(observations=[1,2,3,4])]*6),data)
        p.validate_diagnosis(diagnosis(finding(severity='minor',observations=[]),decision='pass'),payload())
        p.validate_diagnosis(diagnosis(decision='needs_input',question='Which interpreter?'),payload())

    def test_render_numbers_match_validator(self):
        view=json.loads(p.render(payload()))
        self.assertEqual(view['objective_lines'][2],{'line':3,'text':'Docs needed.'})
        self.assertEqual(view['source'][0]['lines'][0],{'line':1,'text':'bad()'})
        self.assertEqual(set(view),{'objective_lines','source','catalog'})


class TransportWiring(unittest.TestCase):
    def setUp(self):
        self.root=Path(tempfile.mkdtemp());self.addCleanup(shutil.rmtree,self.root)

    def ledger(self):return p.create_ledger(self.root,time.monotonic()+150)

    def test_one_precharged_json_only_request(self):
        ledger=self.ledger();transport=FakeTransport(json.dumps(diagnosis(finding())))
        client=p.FinalClient(CONFIG,ledger,transport)
        result=p.finalize(self.root,payload(),client,ledger)
        self.assertEqual(result['status'],'accepted');self.assertEqual(len(transport.calls),1)
        body=transport.calls[0]['body']
        self.assertEqual(body['response_format'],{'type':'json_object'})
        self.assertNotIn('tools',body);self.assertNotIn('tool_choice',body)
        self.assertEqual([m['role'] for m in body['messages']],['system','user'])
        self.assertEqual(body['messages'][1]['content'],p.render(payload()))
        self.assertLessEqual(transport.calls[0]['timeout'],120)
        requests=ledger.read()['requests'];self.assertEqual([r['status'] for r in requests],['returned'])
        with self.assertRaises(RuntimeError):client.complete([{'role':'user','content':'again'}])
        with self.assertRaises(RuntimeError):ledger.reserve('commands',{'command':'ls'})
        self.assertEqual(len(transport.calls),1)

    def test_failed_final_remains_charged_without_retry(self):
        ledger=self.ledger();transport=FakeTransport(error=TimeoutError('slow'))
        client=p.FinalClient(CONFIG,ledger,transport)
        with self.assertRaises(TimeoutError):p.finalize(self.root,payload(),client,ledger)
        self.assertEqual([r['status'] for r in ledger.read()['requests']],['failed'])
        with self.assertRaises(RuntimeError):client.complete([])
        self.assertFalse((self.root/'report.json').exists())

    def test_invalid_model_output_is_not_published(self):
        for content in ['not json',json.dumps(diagnosis(finding(observations=[9]))),json.dumps({**diagnosis(finding()),'repair':'x'})]:
            root=Path(tempfile.mkdtemp());self.addCleanup(shutil.rmtree,root)
            ledger=p.create_ledger(root,time.monotonic()+150);client=p.FinalClient(CONFIG,ledger,FakeTransport(content))
            with self.assertRaises(ValueError):p.finalize(root,payload(),client,ledger)
            self.assertFalse((root/'diagnosis.json').exists())

    def test_explore_phase_ledger_cannot_back_final_client(self):
        p.CaseLedger.create(self.root,time.monotonic()+150)
        with self.assertRaises(ValueError):p.FinalClient(CONFIG,p.CaseLedger(self.root),FakeTransport('{}'))

    def test_expired_deadline_prevents_dispatch(self):
        ledger=p.create_ledger(self.root,time.monotonic()+1);transport=FakeTransport(json.dumps(diagnosis(finding())))
        client=p.FinalClient(CONFIG,ledger,transport);time.sleep(1.1)
        with self.assertRaises(Exception):p.finalize(self.root,payload(),client,ledger)
        self.assertEqual(transport.calls,[])


class RealPackages(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=Path(tempfile.mkdtemp());cls.out=cls.tmp/'pkg'
        cls.manifest=p.prepare(PUBLIC,TRIAL,cls.out)
        cls.sha=p.digest((cls.out/'manifest.json').read_bytes())

    @classmethod
    def tearDownClass(cls):shutil.rmtree(cls.tmp)

    def load(self,case):return json.loads((self.out/case/'payload.json').read_bytes())

    def test_packages_verify_and_exclude_prior_outcomes(self):
        p.verify_packages(self.out/'manifest.json',self.sha)
        for case in ('case-01','case-02','case-03','case-04'):
            value=self.load(case);text=json.dumps(value)
            self.assertEqual(set(value),{'objective','objective_lines','files','catalog'})
            self.assertEqual(set(value['catalog']),{'commands','segments'})
            for marker in ('"decision"','"findings"','"role"','"reasoning_content"','required_finding'):
                self.assertNotIn(marker,text,case)
            trial=TRIAL.parent/case
            for item in json.loads((trial/'verdict.json').read_bytes())['findings']:
                self.assertNotIn(item['evidence'][:80],text,case)
            for response in sorted((trial/'requests').glob('*/response.json')):
                message=json.loads(response.read_bytes())['choices'][0]['message']
                for field in ('content','reasoning_content'):
                    if isinstance(message.get(field),str) and len(message[field].strip())>40:
                        self.assertNotIn(message[field].strip()[:120],text,case)
            private=json.loads((REPO/'evaluations/executable-review/private/expectations.json').read_bytes())
            for entry in private:
                if entry['required_finding']:self.assertNotIn(entry['required_finding'],text)

    def test_catalog_concatenation_is_exact_bounded_feedback(self):
        for case in ('case-01','case-02','case-03','case-04'):
            value=self.load(case);catalog=value['catalog']
            self.assertEqual([s['id'] for s in catalog['segments']],list(range(1,len(catalog['segments'])+1)))
            for command in catalog['commands']:
                text=''.join(s['text'] for s in catalog['segments'] if s['command_id']==command['id'])
                self.assertEqual(p.digest(text.encode()),command['feedback_sha256'])
                self.assertTrue(command['started'] and command['cleanup_confirmed'])
            self.assertTrue(all(len(p.encoded(s['text']))<=2048 for s in catalog['segments']))

    def test_shell_exit_zero_failed_suite_stays_failed_output(self):
        value=self.load('case-01');suite=value['catalog']['commands'][1]
        self.assertEqual(suite['exit_code'],0)
        text=''.join(s['text'] for s in value['catalog']['segments'] if s['command_id']==2)
        self.assertIn('FAILED (errors=1)',text)
        for command in value['catalog']['commands']:
            self.assertFalse({'passed','test_result','suite_passed'}&set(command))

    def test_tampering_fails(self):
        for mutate in ('bytes','mode','binding','extra'):
            with self.subTest(mutate=mutate):
                copy_root=self.tmp/mutate;shutil.copytree(self.out,copy_root)
                target=copy_root/'case-02'/'payload.json'
                if mutate=='bytes':target.write_bytes(target.read_bytes().replace(b'OK',b'KO',1))
                elif mutate=='mode':os.chmod(target,0o666)
                elif mutate=='binding':
                    b=json.loads((copy_root/'case-02'/'binding.json').read_bytes());b['catalog_sha256']='0'*64
                    (copy_root/'case-02'/'binding.json').write_text(json.dumps(b))
                else:(copy_root/'case-02'/'extra.json').write_text('{}')
                with self.assertRaises(ValueError):p.verify_packages(copy_root/'manifest.json',self.sha)

    def test_real_render_within_capacity(self):
        for case in ('case-01','case-02','case-03','case-04'):
            self.assertLess(len(p.render(self.load(case)).encode()),p.CAPACITY)


class LifecycleStops(unittest.TestCase):
    def test_unconfirmed_idle_prevents_any_case(self):
        tmp=Path(tempfile.mkdtemp());self.addCleanup(shutil.rmtree,tmp)
        out=tmp/'pkg';p.prepare(PUBLIC,TRIAL,out);sha=p.digest((out/'manifest.json').read_bytes())
        args=mock.Mock(manifest=str(out/'manifest.json'),manifest_sha256=sha,config=str(tmp/'c.json'),identity=str(tmp/'i.json'),output=str(tmp/'run'),lease=str(tmp/'lease'))
        with mock.patch.object(p,'wait_idle',return_value=False),mock.patch.object(p,'supervise') as supervise:
            results=p.batch(args)
        self.assertEqual([r['status'] for r in results],['not_started']);supervise.assert_not_called()

    def test_uncertain_cleanup_stops_next_case(self):
        tmp=Path(tempfile.mkdtemp());self.addCleanup(shutil.rmtree,tmp)
        out=tmp/'pkg';p.prepare(PUBLIC,TRIAL,out);sha=p.digest((out/'manifest.json').read_bytes())
        args=mock.Mock(manifest=str(out/'manifest.json'),manifest_sha256=sha,config=str(tmp/'c.json'),identity=str(tmp/'i.json'),output=str(tmp/'run'),lease=str(tmp/'lease'))
        outcome={'stop':None,'exit_code':0,'client_group_absent':False,'work_finished_before_deadline':True,'cleanup_deadline':time.monotonic()+1}
        with mock.patch.object(p,'wait_idle',return_value=True),mock.patch.object(p,'supervise',return_value=dict(outcome)) as supervise:
            results=p.batch(args)
        self.assertEqual(len(results),1);self.assertEqual(results[0]['status'],'incomplete');self.assertEqual(supervise.call_count,1)


if __name__=='__main__':unittest.main()
