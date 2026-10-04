"""Independent controlled QA; never connects to a model or Docker."""
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import sys
import time
import unittest
from unittest.mock import patch
from contextlib import ExitStack
from types import SimpleNamespace

spec=importlib.util.spec_from_file_location('pilot',Path(__file__).with_name('planning_pilot_prototype.py'))
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)

class Transport:
 def __init__(self,result=None,error=None):self.calls=0;self.result=result;self.error=error
 def request(self,*args,**kwargs):
  self.calls+=1
  if self.error:raise self.error
  return self.result

class IndependentQA(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
  p.save(self.root/'budget.json',{'limit':48,'calls':[],'deadline':time.monotonic()+60})
 def client(self,transport):return p.BudgetWorker({'endpoint':'http://127.0.0.1:1','model':'qa'},p.Sandbox(),p.Budget(self.root),transport)
 def body(self):return {'model':'qa','temperature':0,'max_tokens':4096,'reasoning_effort':'medium','thinking_budget_tokens':1024,'chat_template_kwargs':{'enable_thinking':True},'messages':[]}
 def test_shared_all_roles_recreation_and_denial(self):
  transport=Transport({'choices':[]})
  roles=['planner','plan_review','implementation','question_assessment','code_review']
  for index in range(48):
   client=self.client(transport);client.next_role=roles[index%5];client.request('/v1/chat/completions',self.body())
  with self.assertRaises(RuntimeError):self.client(transport).request('/v1/chat/completions',self.body())
  self.assertEqual(transport.calls,48);calls=json.loads((self.root/'budget.json').read_text())['calls'];self.assertEqual({c['role']for c in calls},set(roles));self.assertTrue(all(c['status']=='returned'for c in calls))
 def test_failed_transport_and_malformed_completion_remain_charged(self):
  t=Transport(error=TimeoutError('controlled'))
  with self.assertRaises(TimeoutError):self.client(t).request('/v1/chat/completions',self.body())
  malformed=Transport({'choices':[{'message':{'content':'{bad'}}]})
  with self.assertRaises(json.JSONDecodeError):p.completion(self.client(malformed),'planner','system',{})
  calls=p.Budget(self.root).state['calls'];self.assertEqual(len(calls),2);self.assertEqual(calls[0]['status'],'failed');self.assertEqual(calls[1]['status'],'returned')
 def test_deadline_denies_before_transport(self):
  state=p.Budget(self.root).state;state['deadline']=time.monotonic()-1;p.save(self.root/'budget.json',state);t=Transport({})
  with self.assertRaises(TimeoutError):self.client(t).request('/v1/chat/completions',self.body())
  self.assertEqual(t.calls,0)
 def test_profile_changes_denied(self):
  t=Transport({});b=self.body();b['max_tokens']=8192
  with self.assertRaises(ValueError):self.client(t).request('/v1/chat/completions',b)
  self.assertEqual(t.calls,0);self.assertEqual(p.Budget(self.root).state['calls'],[])
 def test_fixed_plan_authority(self):
  case={'requirements':[{'id':'A'},{'id':'B'}],'milestone_requirement_ids':['A']}
  plan={'tasks':[{'id':'task1','objective':'first','requirement_ids':['A'],'depends_on':[]},{'id':'task2','objective':'second','requirement_ids':['B'],'depends_on':['task1']}]}
  self.assertEqual(p.validate_plan(plan,case),plan)
  for mutate in [lambda x:x['tasks'][0].update(checks=[]),lambda x:x['tasks'][1].update(depends_on=[]),lambda x:x['tasks'][1].update(requirement_ids=['A']),lambda x:x['tasks'][0].update(requirement_ids=['A','B'])]:
   bad=json.loads(json.dumps(plan));mutate(bad)
   with self.assertRaises(ValueError):p.validate_plan(bad,case)

 def test_milestone_pass_final_failure_never_promotes(self):
  fixture=Path(__file__).resolve().parents[1]/'evaluations/planning-pilot'
  manifest=json.loads((fixture/'manifest.json').read_text());case=manifest['cases'][0]
  plan={'tasks':[{'id':'task1','objective':'milestone','requirement_ids':case['milestone_requirement_ids'],'depends_on':[]},{'id':'task2','objective':'finish','requirement_ids':[r['id']for r in case['requirements']],'depends_on':['task1']}]}
  p.save(self.root/'config.json',{'endpoint':'http://127.0.0.1:18000','model':'flash-next-coder'});p.save(self.root/'bindings.json',{'python-stdlib':{}})
  p.save(self.root/'spec.json',{'manifest':str(fixture/'manifest.json'),'manifest_sha256':'controlled','case_index':0,'bindings':str(self.root/'bindings.json'),'config':str(self.root/'config.json'),'method':'decomposed'})
  seen=[];outer=self
  class FakeFactory:
   def __init__(self,*a,**kw):pass
   def create(self,path):
    task=json.loads(Path(path).read_text());seen.append(task);identifier=str(len(seen));folder=outer.root/identifier;folder.mkdir();p.save(folder/'task.json',task);return identifier
   def status(self,identifier):return {'status':'accepted','workspace':str(outer.root),'directory':str(outer.root/identifier)}
   def resume(self,identifier):return self.status(identifier)
  class FakeSandbox:
   def __init__(self,*a):pass
   def bind(self,*a):pass
   def verify(self,*a):return {'passed':False}
   def cleanup(self,*a):pass
  with ExitStack()as stack:
   stack.enter_context(patch.dict(os.environ,dict(os.environ),clear=True))
   replacements={'check_manifest':lambda *a:manifest,'resolve_binding':lambda *a:SimpleNamespace(profile='python-stdlib'),'PilotSandbox':FakeSandbox,'PilotFactory':FakeFactory,'BudgetWorker':lambda *a:None,'Reviewer':lambda *a:None,'initialize_repository':lambda *a:'commit','completion':lambda *a:plan if a[1]=='planner'else {'decision':'pass','reason':'controlled'},'checkpoint':lambda *a:{'modes':{},'candidate':'hash'},'checked_tree':lambda *a:{},'fingerprint':lambda *a:'hash','restore_checkpoint':lambda *a:{}}
   for name,value in replacements.items():stack.enter_context(patch.object(p,name,value))
   result=p.arm_work(self.root/'spec.json')
  self.assertEqual(result['status'],'failed');self.assertEqual(result['reason'],'Full acceptance failed');self.assertEqual(len(seen),2)
  self.assertEqual(seen[0]['checks'],case['milestone_checks']);self.assertEqual(seen[1]['checks'],case['full_checks'])
  objective=json.loads((fixture/case['task']).read_text())['objective'];self.assertTrue(all(task['objective'].startswith(objective)for task in seen))
 def test_actual_supervisor_deadline(self):
  result=p.supervise([sys.executable,'-c','import time;time.sleep(30)'],self.root/'deadline.log',time.monotonic()+.2)
  self.assertEqual(result['stop'],'deadline');self.assertIsNotNone(result['exit_code']);self.assertLess(result['work_elapsed_s'],3)
 def test_actual_supervisor_cancellation(self):
  start=time.monotonic()
  result=p.supervise([sys.executable,'-c','import time;time.sleep(30)'],self.root/'cancel.log',start+30,cancelled=lambda:time.monotonic()-start>.2)
  self.assertEqual(result['stop'],'cancelled');self.assertIsNotNone(result['exit_code']);self.assertLess(result['work_elapsed_s'],3)

if __name__=='__main__':unittest.main(verbosity=2)
